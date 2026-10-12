"""Tests for scripts/build_adapters.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build_adapters as ba  # noqa: E402 — must follow the sys.path insert; scripts/ is not a package

try:  # tomllib is stdlib from Python 3.11
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None

SOURCE = """---
description: Review changes before merge
---

Apply `code-review-and-quality`.

Input: $ARGUMENTS

1. Bar-protection scan first (`CLAUDE.md` §4).
"""


@unittest.skipIf(tomllib is None, "needs Python 3.11+ (tomllib)")
class RenderTest(unittest.TestCase):
    def render(self, body: str = SOURCE) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "review.md"
            src.write_text(body, encoding="utf-8")
            desc, text = ba.parse_command(src)
        return tomllib.loads(ba.render_gemini("review", desc, text))

    def test_output_is_valid_toml_with_required_fields(self):
        data = self.render()
        self.assertEqual(set(data), {"description", "prompt"})
        self.assertEqual(data["description"], "Review changes before merge")

    def test_arguments_placeholder_is_translated(self):
        prompt = self.render()["prompt"]
        self.assertIn("{{args}}", prompt)
        self.assertNotIn("$ARGUMENTS", prompt)

    def test_contract_reference_points_at_agents_md(self):
        prompt = self.render()["prompt"]
        self.assertIn("`AGENTS.md` §4", prompt)
        self.assertNotIn("`CLAUDE.md`", prompt)

    def test_preamble_tells_the_agent_to_activate_skills(self):
        self.assertTrue(
            self.render()["prompt"].startswith("This is a Keystone command.")
        )

    def test_triple_quotes_and_backslashes_round_trip(self):
        tricky = SOURCE + "\nRegex: '''a\\d+''' and \"\"\"b\"\"\"\n"
        prompt = self.render(tricky)["prompt"]
        self.assertIn("'''a\\d+'''", prompt)
        self.assertIn('"""b"""', prompt)

    def test_missing_frontmatter_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "bad.md"
            src.write_text("no frontmatter\n", encoding="utf-8")
            with self.assertRaises(ba.SourceError):
                ba.parse_command(src)


class CheckModeTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        (root / "commands").mkdir()
        (root / "commands" / "review.md").write_text(SOURCE, encoding="utf-8")
        self._saved = (ba.ROOT, ba.SOURCE_DIR, ba.GEMINI_DIR, sys.argv)
        ba.ROOT, ba.SOURCE_DIR, ba.GEMINI_DIR = (
            root,
            root / "commands",
            root / "commands" / "keystone",
        )

    def tearDown(self) -> None:
        ba.ROOT, ba.SOURCE_DIR, ba.GEMINI_DIR, sys.argv = self._saved
        self._tmp.cleanup()

    def run_main(self, *args: str) -> int:
        sys.argv = ["build_adapters.py", *args]
        return ba.main()

    def test_check_fails_before_generation_and_passes_after(self):
        self.assertEqual(self.run_main("--check"), 1)
        self.assertEqual(self.run_main(), 0)
        self.assertEqual(self.run_main("--check"), 0)

    def test_editing_the_source_makes_the_adapter_stale(self):
        self.run_main()
        (ba.SOURCE_DIR / "review.md").write_text(
            SOURCE + "\n2. New step.\n", encoding="utf-8"
        )
        self.assertEqual(self.run_main("--check"), 1)

    def test_hand_edited_adapter_is_detected(self):
        self.run_main()
        target = ba.GEMINI_DIR / "review.toml"
        target.write_text(target.read_text() + "\n# hand edit\n", encoding="utf-8")
        self.assertEqual(self.run_main("--check"), 1)

    def test_adapter_without_source_is_an_orphan_and_is_removed(self):
        self.run_main()
        orphan = ba.GEMINI_DIR / "gone.toml"
        orphan.write_text("prompt = 'x'\n", encoding="utf-8")
        self.assertEqual(self.run_main("--check"), 1)
        self.run_main()
        self.assertFalse(orphan.exists())


if __name__ == "__main__":
    unittest.main()
