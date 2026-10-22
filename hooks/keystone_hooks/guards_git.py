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


# --- git.commit-message ------------------------------------------------------

CONVENTIONAL = re.compile(
    r"^(?P<type>[a-z]+)(\((?P<scope>[^()\n]+)\))?(?P<bang>!)?: (?P<subject>\S.*)$"
)
STANDARD_TYPES = {
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "chore",
    "revert",
}
COMMITLINT_FILES = (
    "commitlint.config.js",
    "commitlint.config.cjs",
    "commitlint.config.mjs",
    "commitlint.config.ts",
    ".commitlintrc",
    ".commitlintrc.json",
    ".commitlintrc.yaml",
    ".commitlintrc.yml",
    ".commitlintrc.js",
    ".commitlintrc.cjs",
)
GENERATED_MESSAGE = re.compile(r'^(Merge |Revert "|fixup! |squash! |amend! )')
NOT_PAST_TENSE = {
    "need",
    "embed",
    "feed",
    "seed",
    "speed",
    "proceed",
    "exceed",
    "succeed",
    "shred",
}
NOT_GERUND = {
    "bring",
    "string",
    "ping",
    "ring",
    "thing",
    "spring",
    "swing",
    "sting",
    "ding",
    "wing",
}
HEADER_MAX = 72
# "add parser and fix lexer" is two changes; "add tests and docs" is one.
SECOND_VERB = re.compile(
    r"\band (?:also )?(add|fix|remove|update|refactor|rename|move|bump|drop|change|"
    r"improve|use|make|support|handle|introduce|delete|replace|clean|document|"
    r"implement|enable|disable|migrate|upgrade|revert)\b"
)


def commit_message(args: list[str], cwd: Path) -> str | None:
    """The message a `git commit` will record, or None when git writes it."""
    if any(
        a in args for a in ("--no-edit", "--fixup", "--squash", "-C", "--reuse-message")
    ):
        return None
    if any(a.startswith(("--fixup=", "--squash=", "--reuse-message=")) for a in args):
        return None
    parts: list[str] = []
    i = 0
    while i < len(args):
        token = args[i]
        value = None
        if token in ("-m", "--message", "-F", "--file") and i + 1 < len(args):
            value, i = args[i + 1], i + 1
            if token in ("-F", "--file"):
                value = _read_message_file(value, cwd)
        elif token.startswith("--message="):
            value = token.split("=", 1)[1]
        elif token.startswith("--file="):
            value = _read_message_file(token.split("=", 1)[1], cwd)
        elif re.fullmatch(r"-[A-Za-z]*m.+", token):  # -m"msg" or -amfoo
            value = token[token.index("m") + 1 :]
        elif re.fullmatch(r"-[A-Za-z]*m", token) and i + 1 < len(args):  # -am "msg"
            value, i = args[i + 1], i + 1
        if value is not None:
            parts.append(value)
        i += 1
    return "\n\n".join(parts) if parts else None


def _read_message_file(name: str, cwd: Path) -> str | None:
    if name == "-":
        return None
    path = Path(name) if Path(name).is_absolute() else cwd / name
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def convention(root: Path, setting: str) -> tuple[str, set[str]]:
    """('' when no convention applies, else where it came from), allowed types."""
    if setting == "none":
        return "", set()
    history = git(root, "log", "-n", "20", "--no-merges", "--format=%s").splitlines()
    matches = [m for m in map(CONVENTIONAL.match, history) if m]
    types = STANDARD_TYPES | {m.group("type") for m in matches}
    if setting == "conventional":
        return "configured in .keystone/config.json", types
    if any((root / name).is_file() for name in COMMITLINT_FILES):
        return "commitlint is configured", types
    if len(history) >= 5 and len(matches) >= 0.7 * len(history):
        return f"{len(matches)} of the last {len(history)} commits follow it", types
    return "", set()


def message_problems(message: str, types: set[str]) -> list[str]:
    lines = message.strip("\n").splitlines()
    header = lines[0].strip() if lines else ""
    if GENERATED_MESSAGE.match(header):
        return []
    match = CONVENTIONAL.match(header)
    if not match:
        return [f"header '{header[:60]}' is not `type(scope): summary`"]
    problems = []
    if match.group("type") not in types:
        problems.append(
            f"type '{match.group('type')}' is not one of {', '.join(sorted(types))}"
        )
    if len(header) > HEADER_MAX:
        problems.append(f"header is {len(header)} characters, limit {HEADER_MAX}")
    subject = match.group("subject")
    if subject.endswith("."):
        problems.append("summary ends with a period")
    first = subject.split()[0].lower()
    if (first.endswith("ed") and len(first) > 4 and first not in NOT_PAST_TENSE) or (
        first.endswith("ing") and len(first) > 5 and first not in NOT_GERUND
    ):
        problems.append(
            f"summary starts with '{first}'; use the imperative ('add', not 'added')"
        )
    second = SECOND_VERB.search(subject)
    if second:
        problems.append(
            f"summary joins two actions ('and {second.group(1)}') — if they are "
            "separate changes, split the commit (invariant 6)"
        )
    if len(lines) > 1 and lines[1].strip():
        problems.append("no blank line between header and body")
    return problems


def commit_message_guard(event: Event, ctx: dict) -> list[Finding]:
    findings = []
    for seg in segments(event.command):
        parsed = git_args(seg)
        if parsed is None or parsed[0] != "commit":
            continue
        message = commit_message(parsed[1], event.cwd)
        if message is None:
            continue
        source, types = convention(event.root, ctx["config"].commit_convention)
        if not source:
            continue
        problems = message_problems(message, types)
        if problems:
            findings.append(
                Finding(
                    "git.commit-message",
                    f"commit message breaks the project's convention ({source}): "
                    f"{'; '.join(problems)}. See skills/git-workflow, 'Conventional "
                    "Commits in practice'.",
                )
            )
    return findings


GUARDS = {
    "git.no-verify": no_verify,
    "git.force-push": force_push,
    "git.commit-message": commit_message_guard,
}
