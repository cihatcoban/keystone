#!/usr/bin/env python3
"""Install or remove Keystone's hooks in a harness's settings file.

Claude Code and Codex load the hooks automatically when Keystone is installed
as a plugin; this script is for Gemini CLI, which cannot load them from an
extension without reading another harness's events (ADR-001), and for using a
cloned Keystone without the plugin.

    python3 install_hooks.py gemini                  # ./.gemini/settings.json
    python3 install_hooks.py gemini --scope user     # ~/.gemini/settings.json
    python3 install_hooks.py claude-code             # ./.claude/settings.json
    python3 install_hooks.py codex                   # ./.codex/hooks.json
    python3 install_hooks.py gemini --uninstall
    python3 install_hooks.py gemini --dry-run        # print, write nothing

Existing settings are kept. Earlier Keystone entries are replaced, never
duplicated, and the previous file is saved next to it with a .bak suffix.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_adapters  # noqa: E402 — must follow the sys.path insert; scripts/ is not a package

TARGETS = {
    "claude-code": {
        "project": ".claude/settings.json",
        "user": "~/.claude/settings.json",
    },
    "codex": {"project": ".codex/hooks.json", "user": "~/.codex/hooks.json"},
    "gemini": {"project": ".gemini/settings.json", "user": "~/.gemini/settings.json"},
}
MARKERS = ('/hooks/run.sh" --harness ', '/hooks/keystone_hook.py" --harness ')


def keystone_events(harness: str, keystone_root: Path) -> dict:
    """The harness's hook events with the plugin-root reference made absolute."""
    manifest = json.loads(
        build_adapters.render_hook_manifest(harness, build_adapters.load_registry())
    )
    hooks_dir = keystone_root / "hooks"
    events = manifest["hooks"]
    for groups in events.values():
        for group in groups:
            for handler in group["hooks"]:
                args = handler["command"].split("/hooks/run.sh ", 1)[1]
                if os.name == "nt":  # a plain Windows shell has no POSIX sh
                    script = json.dumps((hooks_dir / "keystone_hook.py").as_posix())
                    handler["command"] = f"python {script} {args}"
                else:
                    script = json.dumps((hooks_dir / "run.sh").as_posix())
                    handler["command"] = f"sh {script} {args}"
    return events


def is_keystone(group: dict) -> bool:
    return any(
        marker in str(h.get("command", ""))
        for h in group.get("hooks", [])
        if isinstance(h, dict)
        for marker in MARKERS
    )


def merge(settings: dict, events: dict, uninstall: bool) -> tuple[dict, int, int]:
    """Settings with Keystone groups replaced; (settings, removed, added)."""
    hooks = settings.setdefault("hooks", {})
    removed = 0
    for event in list(hooks):
        groups = hooks[event] if isinstance(hooks[event], list) else []
        kept = [g for g in groups if not (isinstance(g, dict) and is_keystone(g))]
        removed += len(groups) - len(kept)
        if kept:
            hooks[event] = kept
        else:
            del hooks[event]
    added = 0
    if not uninstall:
        for event, groups in events.items():
            hooks.setdefault(event, []).extend(groups)
            added += len(groups)
    if not hooks:
        del settings["hooks"]
    return settings, removed, added


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("harness", choices=sorted(TARGETS))
    parser.add_argument("--scope", choices=("project", "user"), default="project")
    parser.add_argument("--root", default=".", help="project directory (default: .)")
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    target = TARGETS[args.harness][args.scope]
    path = Path(os.path.expanduser(target))
    if not path.is_absolute():
        path = Path(args.root).resolve() / path
    try:
        settings = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except ValueError as exc:
        print(
            f"ERROR  {path} is not plain JSON ({exc}); edit it by hand — see docs/hooks.md"
        )
        return 1
    if not isinstance(settings, dict):
        print(f"ERROR  {path} must hold a JSON object")
        return 1

    events = keystone_events(args.harness, ROOT)
    settings, removed, added = merge(settings, events, args.uninstall)
    text = json.dumps(settings, indent=2, ensure_ascii=False) + "\n"
    if args.dry_run:
        print(text, end="")
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copy2(path, path.with_name(path.name + ".bak"))
    path.write_text(text, encoding="utf-8")
    verb = "removed" if args.uninstall else "installed"
    print(f"{verb}: {path} ({added} Keystone hook group(s) added, {removed} replaced)")
    if args.harness in ("claude-code", "codex") and not args.uninstall:
        print(
            "Note: the Keystone plugin already loads these hooks in "
            f"{args.harness}; with the plugin installed they would run twice."
        )
    if args.harness == "codex" and not args.uninstall:
        print("Codex runs new hooks only after you trust them: open /hooks in Codex.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
