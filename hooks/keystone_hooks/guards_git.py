"""git.* — git commands that bypass the project's own checks or rewrite history."""

from __future__ import annotations

import fnmatch
import re
import subprocess
from pathlib import Path

from .core import Finding
from .events import Event, git_args, segments

HOOK_BYPASS_ENV = {"HUSKY": "0", "HUSKY_SKIP_HOOKS": "1", "SKIP": None}
VERIFYING = {"commit", "push", "merge", "cherry-pick", "revert", "am", "rebase"}


def git(root: Path, *args: str) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return proc.stdout.strip() if proc.returncode == 0 else ""


VALUE_FLAGS = "mFCc"  # commit flags that consume the next token, e.g. `-m <msg>`


def _short_flags(args: list[str]) -> set[str]:
    """Short flags in `args`; `-m -n` means message "-n", not flag n."""
    flags: set[str] = set()
    skip_next = False
    for token in args:
        if skip_next:
            skip_next = False
            continue
        if token == "--":
            break
        if re.fullmatch(r"-[A-Za-z]+", token):
            for i, ch in enumerate(token[1:], start=1):
                flags.add(ch)
                if ch in VALUE_FLAGS:
                    # `-mfoo` carries its value inline; `-m foo` takes the next token.
                    skip_next = i == len(token) - 1
                    break
    return flags


# --- git.no-verify -----------------------------------------------------------


def no_verify(event: Event, ctx: dict) -> list[Finding]:
    findings = []
    for seg in segments(event.command):
        parsed = git_args(seg)
        if parsed is None:
            continue
        sub, args, settings = parsed
        reasons = []
        if sub in VERIFYING and "--no-verify" in args:
            reasons.append("--no-verify")
        if sub == "commit" and "n" in _short_flags(args):
            reasons.append("-n (no-verify)")
        if any(s.lower().startswith("core.hookspath") for s in settings):
            reasons.append("-c core.hooksPath")
        if sub == "config" and any(a.lower() == "core.hookspath" for a in args):
            reasons.append("git config core.hooksPath")
        if sub in VERIFYING:
            for key, value in HOOK_BYPASS_ENV.items():
                if key in seg.env and (value is None or seg.env[key] == value):
                    reasons.append(f"{key}={seg.env[key]}")
        if reasons:
            findings.append(
                Finding(
                    "git.no-verify",
                    f"`{seg.text[:120]}` bypasses the repository's own hooks "
                    f"({', '.join(reasons)}). Fix what the hook reports instead of "
                    "skipping it (CLAUDE.md §4).",
                )
            )
    return findings


# --- git.force-push ----------------------------------------------------------


def _protected(branch: str, patterns: list[str]) -> bool:
    name = branch.removeprefix("refs/heads/")
    return any(fnmatch.fnmatchcase(name, p) for p in patterns)


def _push_targets(args: list[str], root: Path) -> tuple[list[str], bool]:
    """(destination branches, whether the push forces) for `git push` args."""
    force = any(
        a in ("--force", "--force-with-lease", "--mirror")
        or a.startswith("--force-with-lease=")
        for a in args
    ) or "f" in _short_flags(args)
    deleting = "--delete" in args or "d" in _short_flags(args)
    positional = [a for a in args if not a.startswith("-")]
    refspecs = positional[1:]
    targets = []
    for spec in refspecs:
        if spec.startswith("+"):
            force = True
            spec = spec[1:]
        if spec.startswith(":"):  # ":branch" deletes the remote branch
            force = True
        targets.append(spec.split(":")[-1] if ":" in spec else spec)
    if deleting:
        force = True
    if not targets:
        current = git(root, "rev-parse", "--abbrev-ref", "HEAD")
        targets = [current] if current and current != "HEAD" else []
    return targets, force


def force_push(event: Event, ctx: dict) -> list[Finding]:
    patterns = ctx["config"].protected_branches
    findings = []
    for seg in segments(event.command):
        parsed = git_args(seg)
        if parsed is None or parsed[0] != "push":
            continue
        targets, force = _push_targets(parsed[1], event.root)
        hit = [t for t in targets if _protected(t, patterns)]
        if force and hit:
            findings.append(
                Finding(
                    "git.force-push",
                    f"`{seg.text[:120]}` rewrites or deletes protected branch "
                    f"{', '.join(hit)}. History others have pulled cannot be taken "
                    "back; this needs a human decision (CLAUDE.md §1.3).",
                )
            )
    return findings


GUARDS = {
    "git.no-verify": no_verify,
    "git.force-push": force_push,
}
