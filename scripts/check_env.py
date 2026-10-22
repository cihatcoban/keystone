#!/usr/bin/env python3
"""Configuration and secret hygiene check — stack-agnostic, standard library only.

Run it in any project (not only Keystone):

    python3 /path/to/keystone/scripts/check_env.py            # current directory
    python3 /path/to/keystone/scripts/check_env.py --root DIR
    python3 /path/to/keystone/scripts/check_env.py --strict   # warnings fail too

Errors (exit 1):
  E1  a real env file (.env, .env.local, .env.production ...) is tracked by git
  E2  .env is not ignored by git
  E3  .env.example holds a real-looking value for a secret-named key
  E4  a tracked file contains a string matching a known credential format

Warnings (exit 0 unless --strict):
  W1  .env defines keys that .env.example does not document (drift)
  W2  code reads variables that .env.example does not document
  W3  code reads environment variables but there is no .env.example at all

Test code is excluded from W2/W3 (tests legitimately reference fixture
variables) but not from E4: a real credential in a test is still a leak.

The script never prints a secret value. Matches are reported by location and
credential type only. A line may opt out of E4 with the marker
`keystone:allow-secret` plus a justification in the same comment — that is a
reviewable suppression, see the bar-protection rules in CLAUDE.md §4.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

EXAMPLE_NAMES = (".env.example", ".env.sample", ".env.template", ".env.dist")
SKIP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "target",
    ".gradle",
    ".idea",
}
TEXT_LIMIT_BYTES = 1_000_000
ALLOW_MARKER = "keystone:allow-secret"

SECRET_KEY_NAME = re.compile(
    r"(KEY|SECRET|TOKEN|PASSWORD|PASSWD|PASS|PRIVATE|CREDENTIAL|AUTH)", re.I
)
PLACEHOLDER = re.compile(
    r"^(|changeme|change-me|replace-?me|todo|xxx+|\*+|<[^>]*>|\$\{[^}]*\}|your[-_].*|"
    r"example.*|dummy.*|fake.*|placeholder.*|none|null|test)$",
    re.I,
)
CREDENTIAL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("Anthropic API key", re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}")),
    ("OpenAI API key", re.compile(r"sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}")),
    ("Google API key", re.compile(r"AIza[0-9A-Za-z_-]{35}")),
    (
        "GitHub token",
        re.compile(
            r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,}"
        ),
    ),
    ("AWS access key id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("Slack token", re.compile(r"xox[abprs]-[A-Za-z0-9-]{10,}")),
    (
        "private key block",
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----"),
    ),
]
ENV_READ_PATTERNS = [
    re.compile(r"os\.environ\[\s*['\"]([A-Z][A-Z0-9_]*)['\"]"),
    re.compile(r"os\.(?:environ\.get|getenv)\(\s*['\"]([A-Z][A-Z0-9_]*)['\"]"),
    re.compile(r"process\.env\.([A-Z][A-Z0-9_]*)"),
    re.compile(r"process\.env\[\s*['\"]([A-Z][A-Z0-9_]*)['\"]"),
    re.compile(r"System\.getenv\(\s*\"([A-Z][A-Z0-9_]*)\""),
    re.compile(r"\$\{([A-Z][A-Z0-9_]*)(?::[^}]*)?\}"),  # Spring / shell placeholders
    re.compile(r"os\.(?:Getenv|LookupEnv)\(\s*\"([A-Z][A-Z0-9_]*)\""),
    re.compile(r"env::var\(\s*\"([A-Z][A-Z0-9_]*)\""),
    re.compile(r"ENV\[\s*['\"]([A-Z][A-Z0-9_]*)['\"]"),
    re.compile(r"Environment\.GetEnvironmentVariable\(\s*\"([A-Z][A-Z0-9_]*)\""),
]
CODE_SUFFIXES = {
    ".py",
    ".js",
    ".mjs",
    ".cjs",
    ".ts",
    ".tsx",
    ".jsx",
    ".java",
    ".kt",
    ".go",
    ".rs",
    ".rb",
    ".cs",
    ".php",
    ".yml",
    ".yaml",
    ".properties",
}
# Variables every shell/CI has; reading them does not need documenting.
TEST_DIRS = {"tests", "test", "__tests__", "spec", "specs", "testdata", "fixtures"}
TEST_FILE = re.compile(
    r"(^test_.*|.*_test\.(py|go|rb)|.*\.(test|spec)\.[jt]sx?|.*Tests?\.(java|kt|cs))$"
)
AMBIENT = {
    "HOME",
    "PATH",
    "USER",
    "SHELL",
    "PWD",
    "TMPDIR",
    "TEMP",
    "TMP",
    "LANG",
    "TERM",
    "CI",
    "PORT",
    "HOSTNAME",
    "NODE_ENV",
    "PYTHONPATH",
    "JAVA_HOME",
    "GITHUB_ACTIONS",
    # Set by the agent harness for plugin hooks, never by the project.
    "CLAUDE_PLUGIN_ROOT",
    "PLUGIN_ROOT",
}


@dataclass
class Finding:
    level: str  # ERROR | warn
    code: str
    where: str
    message: str

    def render(self) -> str:
        return f"{self.level:<6} {self.code}  {self.where}: {self.message}"


def is_git_repo(root: Path) -> bool:
    return run_git(root, "rev-parse", "--is-inside-work-tree") == "true"


def run_git(root: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, timeout=30
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def project_files(root: Path, git: bool) -> list[Path]:
    if git:
        listed = run_git(
            root, "ls-files", "-z", "--cached", "--others", "--exclude-standard"
        )
        if listed is not None:
            return [root / p for p in listed.split("\0") if p]
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        files += [Path(dirpath) / f for f in filenames]
    return files


def tracked_files(root: Path, git: bool) -> list[Path]:
    if not git:
        return project_files(root, git=False)
    listed = run_git(root, "ls-files", "-z")
    return [root / p for p in (listed or "").split("\0") if p]


def is_test_file(path: Path, root: Path) -> bool:
    parts = path.relative_to(root).parts
    return any(part in TEST_DIRS for part in parts[:-1]) or bool(
        TEST_FILE.match(path.name)
    )


def is_real_env_file(path: Path) -> bool:
    name = path.name
    if name in EXAMPLE_NAMES:
        return False
    return name == ".env" or name.startswith(".env.") or name.endswith(".env")


def parse_env_keys(path: Path) -> dict[str, str]:
    """KEY -> raw value. Values are only inspected, never printed."""
    entries: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.removeprefix("export ").partition("=")
        value = value.split(" #", 1)[0].strip().strip("'\"")
        entries[key.strip()] = value
    return entries


def read_text(path: Path) -> str | None:
    try:
        if path.stat().st_size > TEXT_LIMIT_BYTES:
            return None
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data[:4096]:
        return None
    return data.decode("utf-8", errors="replace")


def check(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    git = is_git_repo(root)

    def rel(p: Path) -> str:
        return str(p.relative_to(root))

    # E1 — real env files under version control
    tracked = tracked_files(root, git) if git else []
    for path in tracked:
        if is_real_env_file(path):
            findings.append(
                Finding(
                    "ERROR",
                    "E1",
                    rel(path),
                    "env file is tracked by git — remove it from the index and rotate every secret it held",
                )
            )

    # E2 — .env must be ignored
    if git:
        if run_git(root, "check-ignore", "-q", "--no-index", ".env") is None:
            findings.append(
                Finding(
                    "ERROR",
                    "E2",
                    ".gitignore",
                    ".env is not ignored — add `.env` and `.env.*` with `!.env.example`",
                )
            )

    # E3 — example file must not carry real values
    examples = [root / n for n in EXAMPLE_NAMES if (root / n).is_file()]
    documented: set[str] = set()
    for example in examples:
        entries = parse_env_keys(example)
        documented |= set(entries)
        for key, value in entries.items():
            looks_secret = SECRET_KEY_NAME.search(key) and not PLACEHOLDER.match(value)
            matches_format = any(p.search(value) for _, p in CREDENTIAL_PATTERNS)
            if looks_secret or matches_format:
                findings.append(
                    Finding(
                        "ERROR",
                        "E3",
                        f"{rel(example)}:{key}",
                        "has a real-looking value — leave it empty or use a placeholder",
                    )
                )

    # E4 — credential formats anywhere in tracked (or, without git, all) files
    for path in tracked if git else project_files(root, git=False):
        if path.name in EXAMPLE_NAMES or is_real_env_file(path):
            continue  # covered by E1/E3; real env files are never read here
        text = read_text(path)
        if not text:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if ALLOW_MARKER in line:
                continue
            for label, pattern in CREDENTIAL_PATTERNS:
                if pattern.search(line):
                    findings.append(
                        Finding(
                            "ERROR",
                            "E4",
                            f"{rel(path)}:{lineno}",
                            f"looks like a {label} — rotate it, then remove it",
                        )
                    )
                    break

    # W1 — local .env drifted from the documented contract (keys only)
    local_env = root / ".env"
    if local_env.is_file() and examples:
        for key in sorted(set(parse_env_keys(local_env)) - documented):
            findings.append(
                Finding("warn", "W1", f".env:{key}", "not documented in .env.example")
            )

    # W2 / W3 — variables the code reads
    read_by_code: dict[str, str] = {}
    for path in project_files(root, git):
        if path.suffix not in CODE_SUFFIXES or any(
            part in SKIP_DIRS for part in path.parts
        ):
            continue
        if is_test_file(path, root):
            continue
        text = read_text(path)
        if not text:
            continue
        for pattern in ENV_READ_PATTERNS:
            for name in pattern.findall(text):
                read_by_code.setdefault(name, rel(path))
    read_by_code = {k: v for k, v in read_by_code.items() if k not in AMBIENT}
    if read_by_code and not examples:
        findings.append(
            Finding(
                "warn",
                "W3",
                ".",
                f"code reads {len(read_by_code)} environment "
                "variable(s) but there is no .env.example",
            )
        )
    elif examples:
        for name in sorted(set(read_by_code) - documented):
            findings.append(
                Finding(
                    "warn",
                    "W2",
                    read_by_code[name],
                    f"reads {name}, which .env.example does not document",
                )
            )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Configuration and secret hygiene check"
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--strict", action="store_true", help="treat warnings as errors"
    )
    args = parser.parse_args()
    root = args.root.resolve()

    findings = check(root)
    for f in findings:
        print(f.render())
    errors = sum(f.level == "ERROR" for f in findings)
    warnings = len(findings) - errors
    print(f"\ncheck_env: {errors} errors · {warnings} warnings ({root.name})")
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
