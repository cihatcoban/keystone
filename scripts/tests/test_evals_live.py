"""Tests for scripts/evals_live.py, with a fake agent CLI instead of a model."""

from __future__ import annotations

import contextlib
import io
import json
import shlex
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import evals_live as el  # noqa: E402 — must follow the sys.path insert; scripts/ is not a package

FAKE_CLI = """
import json, sys
prompt = sys.argv[1]
if "grading an AI coding agent" in prompt:
    explicit = "Use the git-workflow skill" in prompt
    print("Here is the grade: " + json.dumps({
        "skill_applied": explicit,
        "items": [{"item": "x", "addressed": True}, {"item": "y", "addressed": explicit}],
    }))
else:
    print(json.dumps({"result": "answer to: " + prompt}))
"""


class EvalsLiveTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        fake = Path(self._tmp.name) / "fake_cli.py"
        fake.write_text(FAKE_CLI, encoding="utf-8")
        self.template = (
            f"{shlex.quote(sys.executable)} {shlex.quote(str(fake))} {{prompt}}"
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_checklist_is_read_from_the_skill(self):
        items = el.checklist("git-workflow")
        self.assertGreaterEqual(len(items), 5)
        self.assertTrue(all(not i.startswith("- [ ]") for i in items))

    def test_envelopes_and_grades_are_parsed(self):
        self.assertEqual(el.extract_text('{"result": "hi"}'), "hi")
        self.assertEqual(el.extract_text('{"response": "hi"}'), "hi")
        self.assertEqual(el.extract_text("plain text"), "plain text")
        grade = el.parse_grade('Sure! {"skill_applied": true, "items": []} done')
        self.assertTrue(grade["skill_applied"])
        with self.assertRaises(ValueError):
            el.parse_grade("no json here")

    def test_end_to_end_reports_the_selection_gap(self):
        out = Path(self._tmp.name) / "result.json"
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = el.main(
                [
                    "--command",
                    self.template,
                    "--skills",
                    "git-workflow",
                    "--limit",
                    "1",
                    "--out",
                    str(out),
                ]
            )
        self.assertEqual(code, 0, buffer.getvalue())
        [summary] = json.loads(out.read_text())
        total = len(el.checklist("git-workflow"))
        self.assertEqual(summary["explicit"], round(2 / total, 2))
        self.assertEqual(summary["implicit"], round(1 / total, 2))
        self.assertEqual(summary["applied_rate"], 0.5)
        self.assertIn("git-workflow", buffer.getvalue())

    def test_failing_cli_is_reported_not_crashed(self):
        broken = (
            f"{shlex.quote(sys.executable)} -c 'import sys; sys.exit(4)' {{prompt}}"
        )
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = el.main(["--command", broken, "--skills", "git-workflow"])
        self.assertEqual(code, 1)
        self.assertIn("errored", buffer.getvalue())

    def test_template_needs_a_prompt_placeholder(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            el.main(["--command", "echo hi"])


if __name__ == "__main__":
    unittest.main()
