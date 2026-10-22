"""Tests for scripts/validate_hooks.py: each check must be able to fail."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_hooks as vh  # noqa: E402 — must follow the sys.path insert; scripts/ is not a package

FILES = (
    "CLAUDE.md",
    "hooks/registry.json",
    "docs/hooks.md",
    ".claude-plugin/plugin.json",
    "plugin.json",
)


def load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


class ValidateHooksTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        for name in FILES:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        self.errors: list[str] = []

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def check(self) -> list[str]:
        vh.check(self.root, self.errors.append, load_json)
        return self.errors

    def edit_json(self, name: str, change) -> None:
        path = self.root / name
        data = json.loads(path.read_text(encoding="utf-8"))
        change(data)
        path.write_text(json.dumps(data), encoding="utf-8")

    def test_the_repository_itself_is_clean(self):
        self.assertEqual(self.check(), [])

    def test_default_hooks_file_is_forbidden(self):
        (self.root / "hooks" / "hooks.json").write_text("{}")
        self.assertTrue(any("ADR-001" in e and "hooks.json" in e for e in self.check()))

    def test_unmapped_invariant_fails(self):
        self.edit_json(
            "hooks/registry.json", lambda d: d["review_only_invariants"].pop("2")
        )
        self.assertTrue(any("invariant 2" in e for e in self.check()))

    def test_documented_but_undefined_hook_fails(self):
        doc = self.root / "docs" / "hooks.md"
        text = doc.read_text(encoding="utf-8").replace(
            "## Hook reference", "## Hook reference\n\n| `ghost.hook` | shell |", 1
        )
        doc.write_text(text, encoding="utf-8")
        self.assertTrue(any("ghost.hook" in e for e in self.check()))

    def test_unknown_event_fails(self):
        def rename(d):
            first = next(iter(d["triggers"].values()))
            first["gemini"]["event"] = "PreToolUse"

        self.edit_json("hooks/registry.json", rename)
        self.assertTrue(any("unknown event 'PreToolUse'" in e for e in self.check()))

    def test_manifest_wiring_fails_when_removed(self):
        self.edit_json(".claude-plugin/plugin.json", lambda d: d.pop("hooks"))
        self.assertTrue(any(".claude-plugin/plugin.json" in e for e in self.check()))


if __name__ == "__main__":
    unittest.main()
