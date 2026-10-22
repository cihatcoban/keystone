"""Tests for scripts/verify.py and the verify.stop gate."""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "hooks"))

import build_adapters as ba  # noqa: E402 — must follow the sys.path insert; scripts/ is not a package
import verify  # noqa: E402 — must follow the sys.path insert; scripts/ is not a package
from keystone_hooks import core, events, guards_verify, state  # noqa: E402 — must follow the sys.path insert; hooks/ is not a package

# Shell builtins: verify.py runs commands through the shell, and starting an
# interpreter per step would cost the suite its time budget (CONSTRAINTS.md §4).
OK = "true"
FAIL = "echo boom; exit 3"


def constraints(lint: str = OK, test: str = OK) -> str:
    return f"""# CONSTRAINTS.md

**Change rule:** lowering any number is a standalone change.

## Verification commands

| Phase | Command |
|---|---|
| test | `{test}` |
| types | n/a — none configured |
| lint | `{lint}` |

## 1. Correctness

| Dimension | Threshold | Measured by | Current |
|---|---|---|---|
| Tests | 100% passing | `make test` | 100% |
"""


class Project:
    def __init__(self, text: str) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.git("init", "-q", "-b", "main")
        self.write("CONSTRAINTS.md", text)
        self.write("src/app.py", "x = 1\n")
        self.git("add", ".")
        self.git(
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@example.com",
            "commit",
            "-qm",
            "init",
        )

    def git(self, *args: str) -> None:
        subprocess.run(
            ["git", "-C", str(self.root), *args], check=True, capture_output=True
        )

    def write(self, rel: str, text: str) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def verify(self, *args: str) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = verify.main(["--root", str(self.root), *args])
        return code, out.getvalue()

    def stop(self) -> list[core.Finding]:
        event = events.Event("claude-code", "stop", self.root, self.root)
        ctx = {
            "config": core.Config(),
            "keystone_root": ROOT,
            "constraints_text": (self.root / "CONSTRAINTS.md").read_text(),
        }
        return guards_verify.stop_gate(event, ctx)

    def close(self) -> None:
        self._tmp.cleanup()


class PlanTest(unittest.TestCase):
    def test_explicit_table_in_phase_order_skipping_na(self):
        p = Project(constraints())
        try:
            steps = verify.plan(p.root, (p.root / "CONSTRAINTS.md").read_text(), False)
            self.assertEqual([s.phase for s in steps], ["lint", "test"])
            self.assertEqual({s.origin for s in steps}, {"explicit"})
        finally:
            p.close()

    def test_without_table_only_runnable_commands_are_inferred(self):
        text = constraints().split("## Verification commands")[0] + (
            "## 2. Static analysis\n\n| Check | Threshold | Measured by |\n|---|---|---|\n"
            "| Lint | 0 | `git --version` `no-such-tool-xyz --check` `make lint` |\n"
        )
        p = Project(text)
        try:
            self.assertEqual(verify.plan(p.root, text, False), [])
            inferred = verify.plan(p.root, text, True)
            self.assertEqual(
                [(s.phase, s.command) for s in inferred], [("lint", "git --version")]
            )
            code, out = p.verify()
            self.assertEqual(code, 2)
            self.assertIn("--inferred", out)
        finally:
            p.close()

    def test_no_constraints_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(verify.main(["--root", tmp]), 2)
            self.assertIn("CONSTRAINTS.md", out.getvalue())


class RunTest(unittest.TestCase):
    def test_pass_records_fingerprint_and_satisfies_the_gate(self):
        p = Project(constraints())
        try:
            p.write("src/app.py", "x = 2\n")
            self.assertEqual([f.hook_id for f in p.stop()], ["verify.stop"])
            code, out = p.verify()
            self.assertEqual(code, 0, out)
            stamp = state.read_json(p.root, "verify.json")
            self.assertEqual(stamp["result"], "pass")
            self.assertEqual(p.stop(), [])
            self.assertEqual(
                (p.root / ".keystone/state/.gitignore").read_text().strip()[-1], "*"
            )
            p.write("src/app.py", "x = 3\n")  # an edit after verification
            [finding] = p.stop()
            self.assertIn("changed after the last /verify", finding.message)
        finally:
            p.close()

    def test_failure_is_reported_with_its_tail_and_blocks_the_gate(self):
        p = Project(constraints(test=FAIL))
        try:
            p.write("src/app.py", "x = 2\n")
            code, out = p.verify()
            self.assertEqual(code, 1)
            self.assertIn("FAIL", out)
            self.assertIn("| boom", out)
            [finding] = p.stop()
            self.assertIn("failed", finding.message)
        finally:
            p.close()

    def test_fail_fast_reports_skipped_phases(self):
        p = Project(constraints(lint=FAIL))
        try:
            code, out = p.verify("--fail-fast")
            self.assertEqual(code, 1)
            self.assertIn("SKIPPED", out)
        finally:
            p.close()

    def test_diff_findings_need_acknowledgement(self):
        p = Project(constraints())
        try:
            p.write("src/app.py", "import os  # noqa\n")
            code, out = p.verify()
            self.assertEqual(code, 1)
            self.assertIn("RESULT: REVIEW".lower(), out.lower())
            self.assertIn("bar.suppression", out)
            code, _ = p.verify("--acknowledge", "kept on purpose, see PR #1")
            self.assertEqual(code, 0)
            self.assertEqual(
                state.read_json(p.root, "verify.json")["acknowledged"],
                "kept on purpose, see PR #1",
            )
        finally:
            p.close()

    def test_json_output(self):
        p = Project(constraints())
        try:
            code, out = p.verify("--json", "--no-record")
            self.assertEqual(json.loads(out)["result"], "pass")
            self.assertEqual(state.read_json(p.root, "verify.json"), {})
        finally:
            p.close()


class GateTest(unittest.TestCase):
    def test_clean_tree_and_keystone_files_do_not_fire(self):
        p = Project(constraints())
        try:
            self.assertEqual(p.stop(), [])
            p.write(".keystone/handoff.md", "notes")
            self.assertEqual(p.stop(), [])
        finally:
            p.close()

    def test_no_constraints_no_gate(self):
        p = Project(constraints())
        try:
            (p.root / "CONSTRAINTS.md").unlink()
            event = events.Event("codex", "stop", p.root, p.root)
            ctx = {
                "config": core.Config(),
                "keystone_root": ROOT,
                "constraints_text": "",
            }
            self.assertEqual(guards_verify.stop_gate(event, ctx), [])
        finally:
            p.close()


class AdapterTest(unittest.TestCase):
    def test_gemini_commands_get_an_expanding_root(self):
        prompt = ba.to_gemini_prompt(
            'Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/verify.py"`'
        )
        self.assertIn('"$HOME/.gemini/extensions/keystone/scripts/verify.py"', prompt)
        self.assertNotIn("CLAUDE_PLUGIN_ROOT", prompt)


if __name__ == "__main__":
    unittest.main()
