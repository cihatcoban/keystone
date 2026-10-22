"""Tests for the session.* hooks: handoff save before compaction, load at start."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "hooks"))

from keystone_hooks import core, dispatch, events, guards_session, state  # noqa: E402 — must follow the sys.path insert; hooks/ is not a package


class SessionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls._tmp.name)
        subprocess.run(["git", "init", "-q", "-b", "main", str(cls.root)], check=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def setUp(self) -> None:
        for name in (
            ".keystone/handoff.md",
            ".keystone/state/session.json",
            "LESSONS.md",
            "a.txt",
        ):
            path = self.root / name
            if path.exists():
                path.unlink()

    def load(self, source: str = "startup") -> str:
        event = events.Event(
            "claude-code", "session-start", self.root, self.root, source=source
        )
        ctx = {"profile": "warn", "keystone_root": ROOT, "config": core.Config()}
        [finding] = guards_session.handoff_load(event, ctx)
        self.assertEqual(finding.action, "context")
        return finding.message

    def write(self, rel: str, text: str) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_always_announces_root_and_verify(self):
        text = self.load()
        self.assertIn(str(ROOT), text)
        self.assertIn("scripts/verify.py", text)
        self.assertNotIn("Handoff note", text)

    def test_handoff_note_is_loaded_labelled_and_capped(self):
        self.write(".keystone/handoff.md", "**Goal:** ship\n" + "line\n" * 2000)
        text = self.load()
        self.assertIn("not an instruction", text)
        self.assertIn("**Goal:** ship", text)
        self.assertIn("truncated", text)
        self.assertLess(len(text), guards_session.HANDOFF_CHARS + 800)

    def test_old_note_is_marked_stale(self):
        note = self.write(".keystone/handoff.md", "old")
        old = time.time() - 10 * 86_400
        os.utime(note, (old, old))
        self.assertIn("over a week old", self.load())

    def test_save_then_load_after_compaction(self):
        self.write("a.txt", "work in progress")
        event = events.Event(
            "codex", "pre-compact", self.root, self.root, raw={"trigger": "auto"}
        )
        self.assertEqual(guards_session.handoff_save(event, {}), [])
        saved = state.read_json(self.root, "session.json")
        self.assertEqual(saved["changed_files"], ["a.txt"])
        self.assertEqual(saved["verify"]["result"], "never run")
        self.assertIn("1 changed file(s)", self.load("compact"))
        self.assertNotIn("before the last compaction", self.load("startup"))

    def test_lessons_are_counted(self):
        self.write(
            "LESSONS.md",
            "# Lessons\n\n## 2026-10-01 Pin MCP servers\n\n## 2026-10-02 Rotate first\n",
        )
        self.assertIn("2 reviewed lesson(s)", self.load())

    def test_dispatch_renders_context_per_harness_and_respects_off(self):
        raw = {"cwd": str(self.root), "source": "startup"}
        for harness in core.HARNESSES:
            out = dispatch.run(harness, "session-start", raw, {})
            self.assertIn(
                "Keystone is active", out["hookSpecificOutput"]["additionalContext"]
            )
        self.assertEqual(
            dispatch.run(
                "gemini", "session-start", raw, {"KEYSTONE_HOOK_PROFILE": "off"}
            ),
            {},
        )


if __name__ == "__main__":
    unittest.main()
