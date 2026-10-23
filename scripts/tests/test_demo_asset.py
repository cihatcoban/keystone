"""docs/assets/hooks-demo.svg must show what the hooks really say.

The README's demo is a rendering of real hook output. This test replays the
three actions it shows through the actual dispatcher and fails when a hook's
decision or message no longer matches the picture.
"""

from __future__ import annotations

import html
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SVG = ROOT / "docs" / "assets" / "hooks-demo.svg"

CONSTRAINTS = (
    "# CONSTRAINTS.md\n\n"
    "| Dimension | Threshold | Measured by | Current |\n"
    "|---|---|---|---|\n"
    "| Line coverage | ≥ 80% | `pytest --cov` | 85% |\n"
)
TEST = "def test_refund_limit():\n    assert refund(150) == 422\n"


def svg_text() -> str:
    """All text in the SVG, unescaped and joined with single spaces."""
    raw = SVG.read_text(encoding="utf-8")
    parts = re.findall(r">([^<>]+)<", raw)
    words = (" ".join(html.unescape(p).split()) for p in parts)
    return " ".join(w for w in words if w)


class DemoAssetTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        identity = ["-c", "user.name=t", "-c", "user.email=t@example.com"]
        subprocess.run(
            ["git", "-C", str(self.root), "init", "-q", "-b", "main"], check=True
        )
        (self.root / "CONSTRAINTS.md").write_text(CONSTRAINTS, encoding="utf-8")
        (self.root / "tests").mkdir()
        (self.root / "tests" / "test_refund.py").write_text(TEST, encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "-A"], check=True)
        subprocess.run(
            ["git", "-C", str(self.root), *identity, "commit", "-qm", "init"],
            check=True,
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def hook(self, trigger: str, tool: str, tool_input: dict) -> dict:
        payload = {
            "session_id": "demo",
            "hook_event_name": "PreToolUse",
            "cwd": str(self.root),
            "tool_name": tool,
            "tool_input": tool_input,
        }
        env = {**os.environ, "KEYSTONE_HOOK_PROFILE": "strict"}
        env.pop("KEYSTONE_DISABLED_HOOKS", None)
        proc = subprocess.run(
            [
                "python3",
                str(ROOT / "hooks" / "keystone_hook.py"),
                "--harness",
                "claude-code",
                "--trigger",
                trigger,
            ],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
            check=False,
        )
        return json.loads(proc.stdout)["hookSpecificOutput"]

    def assert_shown(self, out: dict, decision: str, hook_id: str) -> None:
        self.assertEqual(out["permissionDecision"], decision)
        reason = out["permissionDecisionReason"].split("\n(to switch off")[0]
        self.assertTrue(reason.startswith(f"Keystone [{hook_id}]: "))
        message = " ".join(reason.split(": ", 1)[1].split())
        shown = svg_text()
        self.assertIn(hook_id, shown)
        self.assertIn(message, shown)

    def test_lowered_threshold_is_denied_as_shown(self) -> None:
        out = self.hook(
            "edit",
            "Edit",
            {
                "file_path": str(self.root / "CONSTRAINTS.md"),
                "old_string": "| Line coverage | ≥ 80% | `pytest --cov` | 85% |",
                "new_string": "| Line coverage | ≥ 60% | `pytest --cov` | 85% |",
            },
        )
        self.assert_shown(out, "deny", "bar.constraints-lowered")

    def test_skipped_test_is_denied_as_shown(self) -> None:
        out = self.hook(
            "edit",
            "Edit",
            {
                "file_path": str(self.root / "tests" / "test_refund.py"),
                "old_string": "def test_refund_limit():",
                "new_string": '@pytest.mark.skip(reason="flaky")\n'
                "def test_refund_limit():",
            },
        )
        self.assert_shown(out, "deny", "bar.test-weakened")

    def test_force_push_is_denied_as_shown(self) -> None:
        out = self.hook("shell", "Bash", {"command": "git push --force origin main"})
        self.assert_shown(out, "deny", "git.force-push")


if __name__ == "__main__":
    unittest.main()
