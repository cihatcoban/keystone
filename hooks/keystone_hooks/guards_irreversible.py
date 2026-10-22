"""irreversible.command — commands that cannot be taken back (CLAUDE.md §1.3).

Matched per simple command, so `echo "rm -rf /"` is not a deletion and
`cd x && rm -rf data` is. Build output that a rebuild recreates is exempt.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from .core import Finding
from .events import Event, Segment, git_args, segments

REGENERABLE = {
    "node_modules",
    "dist",
    "build",
    "out",
    "target",
    "coverage",
    ".cache",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".next",
    ".turbo",
    ".gradle",
    ".venv",
    "venv",
    ".tox",
    "tmp",
    ".parcel-cache",
}
SQL_DESTRUCTIVE = re.compile(
    r"\b(drop\s+(table|database|schema|index|view|collection)|truncate\s+(table\s+)?\w|"
    r"delete\s+from\s+[\w.\"`]+\s*(;|$|['\"])|alter\s+table\s+\S+\s+drop\b|"
    r"flushall|flushdb|dropdatabase\s*\()",
    re.IGNORECASE,
)
# (program, pattern over the rest of the command line, label)


def _verb(alternatives: str) -> str:
    """Match a whole argument, so a verb inside a path or value does not count."""
    return rf"(?<!\S)({alternatives})(?!\S)"


PROGRAM_RULES: list[tuple[str, re.Pattern[str], str]] = [
    (
        "terraform",
        re.compile(r"\b(destroy|state\s+rm)\b|apply\b.*-auto-approve"),
        "infrastructure change",
    ),
    (
        "tofu",
        re.compile(r"\b(destroy|state\s+rm)\b|apply\b.*-auto-approve"),
        "infrastructure change",
    ),
    (
        "pulumi",
        re.compile(r"\bdestroy\b|\bup\b.*(--yes|-y\b)"),
        "infrastructure change",
    ),
    ("kubectl", re.compile(r"\b(delete|drain|replace\s+--force)\b"), "cluster change"),
    ("helm", re.compile(r"\b(uninstall|delete|rollback)\b"), "cluster change"),
    (
        "docker",
        re.compile(
            r"\b(system|volume|image|container|builder)\s+prune\b|\bvolume\s+rm\b|\bpush\b"
        ),
        "container data",
    ),
    (
        "aws",
        re.compile(_verb(r"rm|rb|delete-\S+|terminate-instances")),
        "cloud resource",
    ),
    ("gcloud", re.compile(_verb("delete")), "cloud resource"),
    ("gsutil", re.compile(_verb("rm|rb")), "cloud resource"),
    ("az", re.compile(_verb("delete")), "cloud resource"),
    ("dropdb", re.compile(r""), "database"),
    ("redis-cli", re.compile(r"\bflush(all|db)\b", re.IGNORECASE), "database"),
    ("npm", re.compile(r"\b(publish|unpublish|deprecate)\b"), "publication"),
    ("pnpm", re.compile(r"\bpublish\b"), "publication"),
    ("yarn", re.compile(r"\b(publish|npm\s+publish)\b"), "publication"),
    ("cargo", re.compile(r"\b(publish|yank)\b"), "publication"),
    ("twine", re.compile(r"\bupload\b"), "publication"),
    ("poetry", re.compile(r"\bpublish\b"), "publication"),
    ("gem", re.compile(r"\b(push|yank)\b"), "publication"),
    ("gh", re.compile(r"\b(release\s+(create|delete)|repo\s+delete)\b"), "publication"),
    ("mvn", re.compile(r"\bdeploy\b"), "publication"),
    ("dd", re.compile(r"\bof=/dev/"), "disk write"),
    ("mkfs", re.compile(r""), "disk format"),
    ("shred", re.compile(r""), "file destruction"),
]
SQL_CLIENTS = {
    "psql",
    "mysql",
    "mariadb",
    "sqlite3",
    "sqlcmd",
    "mongosh",
    "mongo",
    "cockroach",
    "duckdb",
}


def _rm(seg: Segment) -> str:
    args = seg.argv[1:]
    flags = "".join(a[1:] for a in args if re.fullmatch(r"-[A-Za-z]+", a))
    recursive = "r" in flags.lower() or "--recursive" in args
    if not recursive:
        return ""
    targets = [a for a in args if not a.startswith("-")]
    risky = [
        t
        for t in targets
        if t in ("/", "~", "*", ".", "..")
        or PurePosixPath(t.rstrip("/")).name not in REGENERABLE
    ]
    return f"recursive delete of {', '.join(risky[:3])}" if risky else ""


def _git(seg: Segment) -> str:
    parsed = git_args(seg)
    if parsed is None:
        return ""
    sub, args, _ = parsed
    joined = " ".join(args)
    if sub == "reset" and "--hard" in args:
        return "git reset --hard discards uncommitted work"
    if sub == "clean" and re.search(r"(^|\s)(-[a-zA-Z]*f|--force)", joined):
        return "git clean deletes untracked files"
    if sub == "checkout" and ("." in args or "--" in args):
        return "git checkout discards local changes"
    if sub == "restore" and "--staged" not in args and "-S" not in args:
        return "git restore discards local changes"
    if sub == "branch" and re.search(r"(^|\s)-[a-zA-Z]*D|--delete\s+--force", joined):
        return "git branch -D deletes unmerged work"
    if sub == "stash" and args[:1] in (["drop"], ["clear"]):
        return f"git stash {args[0]} deletes stashed work"
    if sub in ("filter-branch", "filter-repo") or (
        sub == "reflog" and "expire" in args
    ):
        return f"git {sub} rewrites history"
    if sub == "push" and "--tags" in args and "--force" in args:
        return "force-pushes tags"
    return ""


def classify(seg: Segment) -> str:
    """Why this simple command is irreversible, or ''."""
    program = PurePosixPath(seg.argv[0]).name
    rest = " ".join(seg.argv[1:])
    if program in ("rm", "rmdir") or (
        program == "find" and re.search(r"-delete\b|-exec\s+rm\b", rest)
    ):
        return (
            _rm(seg)
            if program == "rm"
            else ("find deletes files" if program == "find" else "")
        )
    if program == "git":
        return _git(seg)
    if program in SQL_CLIENTS and SQL_DESTRUCTIVE.search(rest):
        return "destructive SQL"
    for name, pattern, label in PROGRAM_RULES:
        if program == name and pattern.search(rest):
            return f"{label}: {name} {rest[:60]}".strip()
    return ""


def irreversible(event: Event, ctx: dict) -> list[Finding]:
    reasons = [
        (seg.text, why) for seg in segments(event.command) if (why := classify(seg))
    ]
    if not reasons:
        return []
    text, why = reasons[0]
    more = f" (+{len(reasons) - 1} more)" if len(reasons) > 1 else ""
    return [
        Finding(
            "irreversible.command",
            f"`{text[:120]}` — {why}{more}. This cannot be undone; it needs a "
            "human decision even when running unattended (CLAUDE.md §1.3).",
        )
    ]


GUARDS = {"irreversible.command": irreversible}
