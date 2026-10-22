"""Repository checks for the hook layer (ADR-001), called by validate_repo.py.

Kept apart from validate_repo.py so each script stays inside the 400-line
soft limit in CONSTRAINTS.md.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Callable

HOOK_ID = re.compile(r"^[a-z]+\.[a-z0-9-]+$")
HOOK_ACTIONS = {"warn", "ask", "block", "info", "rule"}
HARNESS_EVENTS = {
    "claude-code": {"PreToolUse", "Stop", "PreCompact", "SessionStart", "SessionEnd"},
    "codex": {"PreToolUse", "Stop", "PreCompact", "SessionStart", "SessionEnd"},
    "gemini": {"BeforeTool", "AfterAgent", "PreCompress", "SessionStart", "SessionEnd"},
}
HOOK_WIRING = {
    ".claude-plugin/plugin.json": (("hooks",), "./hooks/claude-code.json"),
    "plugin.json": (("extensions", "com.openai", "hooks"), "./hooks/codex.json"),
}


def invariant_numbers(root: Path) -> set[int]:
    text = (root / "CLAUDE.md").read_text(encoding="utf-8")
    start = text.find("## 1. Invariants")
    end = text.find("\n## ", start + 1)
    return {int(n) for n in re.findall(r"^(\d+)\. \*\*", text[start:end], re.M)}


def documented_hook_ids(text: str) -> set[str] | None:
    """IDs in the first column of the '## Hook reference' table, or None."""
    start = text.find("## Hook reference")
    if start == -1:
        return None
    end = text.find("\n## ", start + 1)
    section = text[start : end if end != -1 else len(text)]
    return set(re.findall(r"^\|\s*`([a-z]+\.[a-z0-9-]+)`", section, re.M))


def check(
    root: Path, err: Callable[[str], None], load_json: Callable[[Path], dict | None]
) -> None:
    if (root / "hooks" / "hooks.json").exists():
        err(
            "hooks/hooks.json must not exist: Claude Code and Gemini CLI both read it, "
            "and each rejects the other's events (ADR-001)"
        )
    registry = load_json(root / "hooks" / "registry.json")
    if registry is None:
        return
    where = "hooks/registry.json"
    triggers = registry.get("triggers", {})
    for name, spec in triggers.items():
        for harness, events in HARNESS_EVENTS.items():
            event = spec.get(harness, {}).get("event")
            if event not in events:
                err(
                    f"{where}: trigger '{name}' maps {harness} to unknown event '{event}'"
                )

    seen: set[str] = set()
    mapped: set[int] = set()
    for hook in registry.get("hooks", []):
        hid = str(hook.get("id", ""))
        if not HOOK_ID.match(hid):
            err(f"{where}: hook id '{hid}' must look like 'family.name'")
        if hid in seen:
            err(f"{where}: duplicate hook id '{hid}'")
        seen.add(hid)
        for trigger in hook.get("trigger", []):
            if trigger not in triggers:
                err(f"{where}: {hid} uses unknown trigger '{trigger}'")
        for profile in ("warn", "strict"):
            if hook.get(profile) not in HOOK_ACTIONS:
                err(f"{where}: {hid} '{profile}' must be one of {sorted(HOOK_ACTIONS)}")
        if not str(hook.get("summary", "")).strip():
            err(f"{where}: {hid} needs a summary")
        mapped |= {int(n) for n in hook.get("invariants", [])}

    review_only = {
        int(k): str(v) for k, v in registry.get("review_only_invariants", {}).items()
    }
    for number in sorted(invariant_numbers(root)):
        if number in mapped and number in review_only:
            err(
                f"{where}: invariant {number} has a hook and is also marked review-only"
            )
        elif number not in mapped and not review_only.get(number, "").strip():
            err(f"{where}: invariant {number} has no hook and no review-only reason")

    # Guards are this repository's code, not data of the tree being validated.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hooks"))
    from keystone_hooks import dispatch

    implemented = set(dispatch.guards())
    for hid in sorted(seen - implemented):
        err(f"{where}: {hid} has no guard function in hooks/keystone_hooks")
    for hid in sorted(implemented - seen):
        err(f"hooks/keystone_hooks: guard '{hid}' is not in {where}")

    doc = root / "docs" / "hooks.md"
    documented = (
        documented_hook_ids(doc.read_text(encoding="utf-8")) if doc.exists() else None
    )
    if documented is None:
        err("docs/hooks.md: missing, or has no '## Hook reference' section")
        documented = set()
    for hid in sorted(seen - documented):
        err(f"docs/hooks.md: hook '{hid}' missing from the Hook reference table")
    for hid in sorted(documented - seen):
        err(f"docs/hooks.md: documents '{hid}', which {where} does not define")

    for manifest, (keys, expected) in HOOK_WIRING.items():
        value = load_json(root / manifest)
        for key in keys:
            value = value.get(key) if isinstance(value, dict) else None
        if value != expected:
            err(f"{manifest}: {'.'.join(keys)} must be '{expected}' (ADR-001)")
