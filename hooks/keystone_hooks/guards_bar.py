"""bar.* — the bar-protection triggers of CLAUDE.md §4, checked as they happen."""

from __future__ import annotations

import fnmatch
import re
from pathlib import PurePosixPath

from . import constraints
from .core import Finding
from .events import Event, FileChange, segments

DOC_SUFFIXES = {".md", ".markdown", ".rst", ".txt", ".adoc"}
CONFIG_SUFFIXES = {
    ".json",
    ".jsonc",
    ".json5",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".xml",
    ".neon",
    ".properties",
    ".cjs",
    ".mjs",
    ".js",
    ".ts",
}
THRESHOLD_WORDS = re.compile(
    r"fail[_-]?under|threshold|min[_-]?coverage|coverage[_-]?min|--cov-fail-under|"
    r"max[_-]?(warnings|complexity|line[_-]?length)",
    re.I,
)
SUPPRESSION = re.compile(
    r"@ts-ignore|@ts-nocheck|@ts-expect-error|eslint-disable|tslint:disable|"
    r"#\s*type:\s*ignore|#\s*noqa|#\s*pylint:\s*disable|#\s*pragma:\s*no\s*cover|"
    r"#\s*pyright:\s*ignore|#\s*nosec|#\[allow\(|@SuppressWarnings|@Suppress\(|"
    r"\[SuppressMessage|#pragma\s+warning\s+disable|//\s*nolint|NOSONAR|"
    r"rubocop:disable|swiftlint:disable|@phpstan-ignore|@psalm-suppress|"
    r"biome-ignore|deno-lint-ignore|stylelint-disable|prettier-ignore"
)
TRACKING_LINK = re.compile(
    r"https?://\S+|(?<![\w/])#\d+\b|\b[A-Z][A-Z0-9]+-\d+\b|\bGH-\d+\b"
)
TEST_DIR_PARTS = {"test", "tests", "__tests__", "spec", "specs", "testing", "e2e"}
TEST_FILE = re.compile(
    r"^(test_.+|.+_test\.\w+|.+\.(test|spec)\.\w+|.+Tests?\.\w+|.+_spec\.\w+|.+Spec\.\w+)$"
)
SKIP_OR_FOCUS = re.compile(
    r"\.skip\s*\(|\bx(it|describe|test)\s*\(|\.only\s*\(|\bf(it|describe)\s*\(|"
    r"@pytest\.mark\.(skip|xfail)|@unittest\.skip|\bpytest\.skip\(|\.skipTest\(|"
    r"@Disabled\b|@Ignore\b|\bt\.Skip(Now|f)?\(|#\[ignore\]|\bpending\s*\(|"
    r"\b(test|it)\.todo\(|\[Ignore\]|Skip\s*=\s*\"|markTestSkipped|\.skipIf\("
)
TEST_DEFINITION = re.compile(
    r"^\s*(async\s+)?def\s+test\w*|^\s*(it|test|specify)\s*\(|^\s*func\s+Test\w+|"
    r"@Test\b|#\[test\]|\[(Fact|Theory|Test|TestMethod)\b|^\s*(it|test)\s+['\"]",
    re.M,
)
ASSERTION = re.compile(
    r"\bassert\w*\b|\bexpect\s*\(|\.should\b|\bAssert\.|\brequire\.\w+\(|\bt\.(Error|Fatal)f?\(",
)
REMOVE_COMMANDS = {"rm", "unlink", "del", "rmdir", "Remove-Item", "shred"}


def is_test_path(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return bool(TEST_DIR_PARTS & {p.lower() for p in parts[:-1]}) or bool(
        TEST_FILE.match(parts[-1] if parts else "")
    )


def _suffix(path: str) -> str:
    return PurePosixPath(path).suffix.lower()


# --- bar.constraints-lowered -------------------------------------------------


def constraints_lowered(event: Event, ctx: dict) -> list[Finding]:
    findings = []
    for change in event.changes:
        if PurePosixPath(change.path).name != "CONSTRAINTS.md":
            continue
        disk = constraints.load(event.root) if change.path == "CONSTRAINTS.md" else ""
        fallback = constraints.headers_by_row(disk or change.before)
        old_rows = constraints.table_rows(change.before, fallback)
        new_rows = constraints.table_rows(change.after, fallback)
        reasons = []
        for key, old in old_rows.items():
            new = new_rows.get(key)
            if new is None:
                if change.whole_file or change.deleted:
                    reasons.append(f"row '{old.cells[0]}' removed")
                continue
            reasons += constraints.loosened(old, new)
        if change.deleted:
            reasons.append("CONSTRAINTS.md deleted")
        if reasons:
            findings.append(
                Finding(
                    "bar.constraints-lowered",
                    f"{change.path} loosens the quality bar: {'; '.join(reasons[:5])}. "
                    "Lowering a number is a standalone change with its own "
                    "justification, never part of a feature (CLAUDE.md §4).",
                )
            )
    return findings


# --- bar.check-config --------------------------------------------------------


def _config_like(path: str) -> bool:
    name = PurePosixPath(path).name.lower()
    return (
        name.startswith(".")
        or _suffix(path) in CONFIG_SUFFIXES
        or "config" in name
        or name.endswith("rc")
    ) and _suffix(path) not in DOC_SUFFIXES


def check_config(event: Event, ctx: dict) -> list[Finding]:
    text = ctx.get("constraints_text", "")
    stems = constraints.tool_stems(text) if text else set()
    protected = ctx["config"].protected_paths
    findings = []
    for change in event.changes:
        path = change.path
        name = PurePosixPath(path).name.lower()
        why = ""
        if any(fnmatch.fnmatch(path, glob) for glob in protected):
            why = "is listed in protected_paths"
        elif _config_like(path) and name != "constraints.md":
            hit = sorted(s for s in stems if s in name)
            if hit:
                why = f"configures {', '.join(hit)}, which CONSTRAINTS.md measures with"
            else:
                changed = "\n".join(change.added_lines() + change.removed_lines())
                words = sorted(
                    s for s in stems if re.search(rf"\b{re.escape(s)}\b", changed)
                )
                if words or THRESHOLD_WORDS.search(changed):
                    why = "changes settings of a check CONSTRAINTS.md relies on"
        if why:
            findings.append(
                Finding(
                    "bar.check-config",
                    f"{path} {why}. Tightening a check is fine; loosening it inside "
                    "a feature change is a bar-protection trigger (CLAUDE.md §4).",
                )
            )
    return findings


# --- bar.suppression ---------------------------------------------------------


def suppression(event: Event, ctx: dict) -> list[Finding]:
    findings = []
    for change in event.changes:
        if _suffix(change.path) in DOC_SUFFIXES:
            continue  # documentation quotes markers; it does not apply them
        bare = [
            line.strip()
            for line in change.added_lines()
            if SUPPRESSION.search(line) and not TRACKING_LINK.search(line)
        ]
        if bare:
            sample = bare[0][:100]
            findings.append(
                Finding(
                    "bar.suppression",
                    f"{change.path} adds {len(bare)} suppression(s) without a "
                    f"justification and tracking link, e.g. `{sample}`. Fix the "
                    "finding, or add the reason and an issue link on the same line.",
                )
            )
    return findings


# --- bar.test-weakened -------------------------------------------------------


def _weakened(change: FileChange) -> list[str]:
    if change.deleted:
        return ["deletes the test file"]
    reasons = []
    skips = [line for line in change.added_lines() if SKIP_OR_FOCUS.search(line)]
    if skips:
        reasons.append(f"adds skip/focus markers (`{skips[0].strip()[:80]}`)")
    removed = len(TEST_DEFINITION.findall(change.before)) - len(
        TEST_DEFINITION.findall(change.after)
    )
    if removed > 0:
        reasons.append(f"removes {removed} test(s)")
    elif change.before.strip():
        fewer = len(ASSERTION.findall(change.before)) - len(
            ASSERTION.findall(change.after)
        )
        if fewer > 0:
            reasons.append(f"removes {fewer} assertion(s)")
    return reasons


def test_weakened(event: Event, ctx: dict) -> list[Finding]:
    findings = []
    if event.trigger == "edit":
        for change in event.changes:
            if not is_test_path(change.path):
                continue
            reasons = _weakened(change)
            if reasons:
                findings.append(
                    Finding(
                        "bar.test-weakened",
                        f"{change.path} {' and '.join(reasons)}. A skipped, removed or "
                        "weakened test converts a failure into silence (CLAUDE.md §4).",
                    )
                )
        return findings
    for seg in segments(event.command):
        argv = seg.argv
        name = PurePosixPath(argv[0]).name
        targets = argv[1:]
        if name == "git" and len(argv) > 1 and argv[1] == "rm":
            targets = argv[2:]
        elif name not in REMOVE_COMMANDS:
            continue
        tests = [
            t
            for t in targets
            if not t.startswith("-")
            and (is_test_path(t) or PurePosixPath(t).name.lower() in TEST_DIR_PARTS)
        ]
        if tests:
            findings.append(
                Finding(
                    "bar.test-weakened",
                    f"`{seg.text[:120]}` deletes test files ({', '.join(tests[:3])}). "
                    "Deleting a test is a bar-protection trigger (CLAUDE.md §4).",
                )
            )
    return findings


GUARDS = {
    "bar.constraints-lowered": constraints_lowered,
    "bar.check-config": check_config,
    "bar.suppression": suppression,
    "bar.test-weakened": test_weakened,
}
