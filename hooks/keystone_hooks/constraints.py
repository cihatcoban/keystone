"""Read a project's CONSTRAINTS.md: thresholds, measuring tools, verify commands."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

NON_THRESHOLD_COLUMNS = {
    "current",
    "status",
    "measured by",
    "enforced by",
    "where to look",
}
HIGHER_IS_STRICTER = re.compile(r"(≥|>=|\bat least\b|\bminimum\b|\bmin\b)", re.I)
LOWER_IS_STRICTER = re.compile(
    r"(≤|<=|<|\bat most\b|\bmaximum\b|\bmax\b|\bunder\b|\bbelow\b|\bwithin\b)", re.I
)
NUMBER = re.compile(
    r"(?<![\w.])(\d[\d,]*(?:\.\d+)?)\s*(%|ms|s|min|tokens|lines|words|kb|mb)?", re.I
)
# Words that run a tool rather than name one: skip them to find the tool.
RUNNERS = {
    "make",
    "npx",
    "npm",
    "pnpm",
    "yarn",
    "bun",
    "bunx",
    "uv",
    "uvx",
    "poetry",
    "pipx",
    "python",
    "python3",
    "py",
    "node",
    "go",
    "cargo",
    "dotnet",
    "gradle",
    "mvn",
    "./gradlew",
    "./mvnw",
    "bundle",
    "exec",
    "run",
    "run-script",
    "-m",
    "time",
    "sh",
    "bash",
    "pre-commit",
    "tox",
    "nox",
    "just",
    "task",
    "dlx",
}
# Make targets and package scripts name a step, not a tool: `make test` says
# nothing about which config file configures the tests.
GENERIC_NAMES = {
    "all",
    "audit",
    "build",
    "check",
    "ci",
    "dev",
    "fmt",
    "format",
    "install",
    "lint",
    "run",
    "start",
    "test",
    "tests",
    "typecheck",
    "types",
    "validate",
    "verify",
    "vet",
    "default",
}
PHASES = ("build", "types", "lint", "test", "security")


@dataclass
class Row:
    header: list[str]
    cells: list[str]

    @property
    def key(self) -> str:
        return self.cells[0].strip().lower() if self.cells else ""

    def threshold_cells(self) -> list[tuple[str, str]]:
        """(column name, cell) for columns that hold a threshold."""
        out = []
        for i, cell in enumerate(self.cells[1:], start=1):
            name = self.header[i].strip().lower() if i < len(self.header) else ""
            if name not in NON_THRESHOLD_COLUMNS:
                out.append((name, cell))
        return out


def split_row(line: str) -> list[str]:
    inner = line.strip().strip("|")
    return [c.strip() for c in re.split(r"(?<!\\)\|", inner)]


def is_separator(line: str) -> bool:
    return bool(re.fullmatch(r"\|?[\s:|-]+\|?", line.strip())) and "-" in line


def table_rows(
    text: str, fallback_header: dict[str, list[str]] | None = None
) -> dict[str, Row]:
    """Rows of every markdown table, keyed by first cell, with their header."""
    rows: dict[str, Row] = {}
    lines = text.splitlines()
    header: list[str] = []
    for i, line in enumerate(lines):
        if not line.strip().startswith("|"):
            header = []
            continue
        if is_separator(line):
            continue
        cells = split_row(line)
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if is_separator(nxt):
            header = cells
            continue
        row_header = header or (fallback_header or {}).get(cells[0].strip().lower(), [])
        rows[cells[0].strip().lower()] = Row(row_header, cells)
    return rows


def numbers(cell: str) -> list[tuple[float, bool]]:
    """(value, higher_is_stricter) for each number in a threshold cell."""
    out = []
    for match in NUMBER.finditer(cell):
        value = float(match.group(1).replace(",", ""))
        before = cell[: match.start()]
        if HIGHER_IS_STRICTER.search(before[-12:]):
            higher = True
        elif LOWER_IS_STRICTER.search(before[-12:]):
            higher = False
        else:
            higher = (
                match.group(2) == "%"
            )  # "100% passing"; bare counts: fewer is stricter
        out.append((value, higher))
    return out


def loosened(old: Row, new: Row) -> list[str]:
    """Human-readable reasons a row became more permissive."""
    reasons = []
    new_cells = dict(new.threshold_cells())
    for name, old_cell in old.threshold_cells():
        new_cell = new_cells.get(name)
        if new_cell is None or new_cell == old_cell:
            continue
        old_nums, new_nums = numbers(old_cell), numbers(new_cell)
        if old_nums and not new_nums:
            reasons.append(
                f"'{old.cells[0]}': '{old_cell}' → '{new_cell}' drops the number"
            )
            continue
        for (ov, higher), (nv, _) in zip(old_nums, new_nums):
            if (higher and nv < ov) or (not higher and nv > ov):
                reasons.append(f"'{old.cells[0]}': '{old_cell}' → '{new_cell}'")
                break
    return reasons


def headers_by_row(text: str) -> dict[str, list[str]]:
    return {key: row.header for key, row in table_rows(text).items()}


def backticked(text: str) -> list[str]:
    return [m.strip() for m in re.findall(r"`([^`\n]+)`", text)]


def measured_by(text: str) -> list[str]:
    """Backticked spans in every 'Measured by' or 'Enforced by' cell."""
    spans = []
    for row in table_rows(text).values():
        for i, cell in enumerate(row.cells):
            name = row.header[i].strip().lower() if i < len(row.header) else ""
            if name in ("measured by", "enforced by"):
                spans += backticked(cell)
    return spans


def tool_name(span: str) -> str:
    """'npx --yes markdownlint-cli2@0.22.1' -> 'markdownlint-cli2'."""
    for token in span.split():
        if token.startswith("-") or token in RUNNERS or "=" in token:
            continue
        name = (
            token.split("@")[0]
            if not token.startswith("@")
            else token.rsplit("@", 1)[0]
        )
        name = Path(name).name
        name = re.sub(r"\.(py|sh|js|mjs|ts|rb|pl)$", "", name)
        return name.lower()
    return ""


def tool_stems(text: str) -> set[str]:
    """Names to look for in config file names, e.g. {'ruff', 'markdownlint'}."""
    stems: set[str] = set()
    for span in measured_by(text) + [cmd for _, cmd in verification_commands(text)]:
        name = tool_name(span)
        for stem in (name, re.split(r"[-_]", name)[0]):
            if len(stem) >= 4 and stem not in GENERIC_NAMES:
                stems.add(stem)
    return stems


def verification_commands(text: str) -> list[tuple[str, str]]:
    """(phase, command) from a '## Verification commands' table, in file order."""
    match = re.search(
        r"^##+\s*(?:\d+\.\s*)?Verification commands\s*$", text, re.M | re.I
    )
    if not match:
        return []
    section = text[match.end() :]
    end = re.search(r"^##\s", section, re.M)
    section = section[: end.start()] if end else section
    out = []
    for row in table_rows(section).values():
        if len(row.cells) < 2:
            continue
        phase = row.cells[0].strip().lower()
        for command in backticked(row.cells[1]):
            out.append((phase, command))
    return out


def load(root: Path) -> str:
    path = root / "CONSTRAINTS.md"
    try:
        return path.read_text(encoding="utf-8") if path.is_file() else ""
    except OSError:
        return ""
