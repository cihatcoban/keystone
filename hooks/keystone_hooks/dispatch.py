"""Run every enabled guard for one trigger and print the harness's answer."""

from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path
from typing import Callable

from . import constraints
from .core import (
    HARNESSES,
    KEYSTONE_ROOT,
    SEVERITY,
    TRIGGERS,
    Finding,
    adapt_to_harness,
    find_root,
    format_message,
    load_config,
    load_registry,
    render,
    resolve_action,
)
from .events import normalize

# Each module exports GUARDS: {hook_id: function(event, ctx) -> list[Finding]}.
GUARD_MODULES: list[str] = []

Guard = Callable[..., list]


def guards() -> dict[str, Guard]:
    table: dict[str, Guard] = {}
    for name in GUARD_MODULES:
        table.update(importlib.import_module(f"{__package__}.{name}").GUARDS)
    return table


def debug(message: str) -> None:
    if os.environ.get("KEYSTONE_HOOK_DEBUG"):
        print(f"keystone-hook: {message}", file=sys.stderr)


def run(harness: str, trigger: str, raw: dict, env: dict | None = None) -> dict:
    """Pure entry point used by the CLI and by tests."""
    cwd = Path(str(raw.get("cwd") or os.getcwd()))
    root = find_root(cwd)
    config = load_config(root, env)
    for note in config.notes:
        debug(note)
    if config.profile == "off":
        return {}
    registry = load_registry()
    table = guards()
    event = normalize(harness, trigger, raw, root)
    ctx = {
        "config": config,
        "profile": config.profile,
        "keystone_root": KEYSTONE_ROOT,
        "constraints_text": constraints.load(root),
    }
    resolved: list[tuple[str, str, str]] = []  # (action, hook_id, message)
    for entry in registry["hooks"]:
        hook_id = entry["id"]
        if trigger not in entry["trigger"] or config.is_disabled(hook_id):
            continue
        guard = table.get(hook_id)
        if guard is None:
            debug(f"no guard registered for {hook_id}")
            continue
        try:
            found: list[Finding] = guard(event, ctx)
        except Exception as exc:  # a broken guard must never break the session
            debug(f"{hook_id} failed open: {exc!r}")
            continue
        for finding in found:
            if config.is_disabled(finding.hook_id):
                continue
            action = resolve_action(entry, config.profile, finding)
            action = adapt_to_harness(action, harness, config.profile)
            resolved.append((action, finding.hook_id, finding.message))

    if trigger == "session-start":
        context = "\n\n".join(m for a, _, m in resolved if a in ("context", "info"))
        return render(harness, trigger, "context", "", context)
    if not resolved:
        return {}
    top = max(SEVERITY[a] for a, _, _ in resolved)
    action = next(a for a in ("block", "ask", "warn", "info") if SEVERITY[a] == top)
    if trigger == "stop" and action == "block" and event.stop_hook_active:
        action = "warn"  # already asked to continue once; do not loop
    shown = [(h, m) for a, h, m in resolved if SEVERITY[a] >= 1] or [
        (h, m) for _, h, m in resolved
    ]
    return render(harness, trigger, action, format_message(shown))


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="keystone_hook")
    parser.add_argument("--harness", required=True, choices=HARNESSES)
    parser.add_argument("--trigger", required=True, choices=TRIGGERS)
    args = parser.parse_args(argv)
    try:
        data = sys.stdin.read()
        raw = json.loads(data) if data.strip() else {}
        if not isinstance(raw, dict):
            raw = {}
    except (OSError, ValueError) as exc:
        debug(f"unreadable hook input: {exc}")
        raw = {}
    try:
        out = run(args.harness, args.trigger, raw)
    except Exception as exc:  # fail open: an unusable hook says nothing
        debug(f"failed open: {exc!r}")
        out = {}
    if out:
        sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
    return 0
