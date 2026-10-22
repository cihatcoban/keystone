"""secret.* — credential-shaped strings about to enter a file or a commit.

Patterns come from scripts/check_env.py so the hook and the CI check can never
disagree about what a credential looks like. Messages name the credential type
and location only; a hook never echoes a secret value.
"""

from __future__ import annotations

import math
import re
import sys
from collections import Counter
from pathlib import PurePosixPath

from .core import KEYSTONE_ROOT, Finding
from .events import Event, git_args, segments
from .guards_git import git

sys.path.insert(0, str(KEYSTONE_ROOT / "scripts"))
import check_env  # noqa: E402 — needs the sys.path insert above; scripts/ is not a package

GENERIC_ASSIGNMENT = re.compile(
    r"(?i)\b[\w.-]*(password|passwd|secret|token|api[_-]?key|private[_-]?key)[\w.-]*"
    r"\s*[:=]\s*['\"]([^'\"\s]{16,})['\"]"
)
EXAMPLE_FILES = re.compile(r"\.(example|sample|template|dist)$|\.example\.", re.I)


def entropy(value: str) -> float:
    counts = Counter(value)
    return -sum(n / len(value) * math.log2(n / len(value)) for n in counts.values())


def credential_types(lines: list[str]) -> list[str]:
    """Credential types found in `lines`, skipping lines marked allowed."""
    found = []
    for line in lines:
        if check_env.ALLOW_MARKER in line:
            continue
        for label, pattern in check_env.CREDENTIAL_PATTERNS:
            if pattern.search(line):
                found.append(label)
        for match in GENERIC_ASSIGNMENT.finditer(line):
            value = match.group(2)
            if not check_env.PLACEHOLDER.match(value) and entropy(value) >= 3.5:
                found.append(f"high-entropy {match.group(1).lower()} value")
    return found


def _summary(types: list[str]) -> str:
    return ", ".join(f"{n}× {t}" for t, n in Counter(types).most_common())


def secret_write(event: Event, ctx: dict) -> list[Finding]:
    findings = []
    for change in event.changes:
        if EXAMPLE_FILES.search(PurePosixPath(change.path).name):
            types = [
                t for t in credential_types(change.added_lines()) if "entropy" not in t
            ]
        else:
            types = credential_types(change.added_lines())
        if types:
            findings.append(
                Finding(
                    "secret.write",
                    f"{change.path} would contain a credential ({_summary(types)}). "
                    "Read it from the environment instead and document the variable "
                    "in .env.example (skills/configuration-and-secrets).",
                )
            )
    return findings


def secret_staged(event: Event, ctx: dict) -> list[Finding]:
    commits = [
        seg
        for seg in segments(event.command)
        if (git_args(seg) or ("",))[0] == "commit"
    ]
    if not commits:
        return []
    args = git_args(commits[0])[1]
    # `git commit -a` stages tracked changes as part of the commit.
    stage_all = "--all" in args or any(
        re.fullmatch(r"-[A-Za-z]*a[A-Za-z]*", a) for a in args
    )
    diff = git(event.root, "diff", "--cached", "--unified=0", "--no-color")
    if stage_all:
        diff += "\n" + git(event.root, "diff", "--unified=0", "--no-color")
    added = [
        line[1:]
        for line in diff.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]
    types = credential_types(added)
    if not types:
        return []
    return [
        Finding(
            "secret.staged",
            f"the commit would record a credential ({_summary(types)}). Unstage it, "
            "rotate it if it was ever real, and load it from the environment.",
        )
    ]


GUARDS = {
    "secret.staged": secret_staged,
    "secret.write": secret_write,
}
