"""rules.project — a project's own prohibitions, written as markdown files.

    .keystone/rules/no-raw-sql.md
    ---
    name: no-raw-sql
    trigger: edit                 # shell | edit | any
    pattern: \\bdb\\.raw\\(       # Python regex
    paths: src/**, !src/db/**     # edit only; '!' excludes; default: every file
    action: block                 # warn | ask | block (default warn)
    ---
    Raw SQL bypasses the repository layer. Use the query builder in src/db.

For `edit` the pattern is matched against the lines a change adds; for `shell`
against the command. The body is the message the agent sees. A rule is the
team's explicit decision, so its action holds in both `warn` and `strict`.
"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from pathlib import Path

from .core import Finding
from .events import Event

ACTIONS = {"warn", "ask", "block"}
NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")


@dataclass
class Rule:
    name: str
    trigger: str
    pattern: re.Pattern[str]
    paths: list[str]
    action: str
    message: str

    def applies_to(self, path: str) -> bool:
        include = [p for p in self.paths if not p.startswith("!")]
        exclude = [p[1:] for p in self.paths if p.startswith("!")]
        if include and not any(fnmatch.fnmatch(path, p) for p in include):
            return False
        return not any(fnmatch.fnmatch(path, p) for p in exclude)


def parse_rule(path: Path) -> tuple[Rule | None, str]:
    """(rule, problem). A broken rule is reported, never half-applied."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"{path.name}: unreadable ({exc})"
    match = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not match:
        return None, f"{path.name}: missing frontmatter"
    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            value = re.sub(r"\s+#.*$", "", value.strip())
            meta[key.strip().lower()] = value
    if meta.get("enabled", "true").lower() == "false":
        return None, ""
    name = meta.get("name") or path.stem
    trigger = meta.get("trigger", "any").lower()
    action = meta.get("action", "warn").lower()
    if not NAME.match(name):
        return (
            None,
            f"{path.name}: name '{name}' must be lowercase letters, digits, dashes",
        )
    if trigger not in ("shell", "edit", "any"):
        return None, f"{path.name}: trigger must be shell, edit or any"
    if action not in ACTIONS:
        return None, f"{path.name}: action must be warn, ask or block"
    try:
        pattern = re.compile(meta.get("pattern", ""))
    except re.error as exc:
        return None, f"{path.name}: invalid pattern ({exc})"
    if not pattern.pattern:
        return None, f"{path.name}: pattern is required"
    paths = [p.strip() for p in meta.get("paths", "").split(",") if p.strip()]
    body = match.group(2).strip() or f"matches project rule {name}"
    return Rule(name, trigger, pattern, paths, action, body), ""


def load_rules(root: Path) -> tuple[list[Rule], list[str]]:
    rules, problems = [], []
    for path in sorted((root / ".keystone" / "rules").glob("*.md")):
        rule, problem = parse_rule(path)
        if rule:
            rules.append(rule)
        if problem:
            problems.append(problem)
    return rules, problems


def project_rules(event: Event, ctx: dict) -> list[Finding]:
    rules, problems = load_rules(event.root)
    findings = []
    for rule in rules:
        if rule.trigger not in (event.trigger, "any"):
            continue
        where = ""
        if event.trigger == "shell" and rule.pattern.search(event.command):
            where = f"`{event.command[:100]}`"
        for change in event.changes:
            if rule.applies_to(change.path) and any(
                rule.pattern.search(line) for line in change.added_lines()
            ):
                where = change.path
                break
        if where:
            findings.append(
                Finding(
                    f"rules.project/{rule.name}",
                    f"{where}: {rule.message}",
                    rule.action,
                )
            )
    if problems:
        findings.append(
            Finding(
                "rules.project",
                "rules skipped — " + "; ".join(problems[:3]),
                "warn",
            )
        )
    return findings


GUARDS = {"rules.project": project_rules}
