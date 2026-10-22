"""Tests for scripts/install_agents.py (Cursor, opencode, Copilot)."""

from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import install_agents as ia  # noqa: E402 — must follow the sys.path insert; scripts/ is not a package

ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS = sorted(
    d.name for d in (ROOT / "skills").iterdir() if (d / "SKILL.md").exists()
)
COMMANDS = sorted(p.stem for p in (ROOT / "commands").glob("*.md"))
AGENTS = sorted(p.name for p in (ROOT / "agents").glob("*.md"))


class InstallAgentsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_cli(self, *args: str) -> str:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(ia.main([*args, "--root", str(self.root)]), 0)
        return out.getvalue()

    def test_opencode_gets_skills_commands_and_subagents(self):
        self.run_cli("opencode")
        skills = self.root / ".agents" / "skills"
        self.assertEqual(sorted(p.name for p in skills.iterdir()), SKILLS)
        self.assertTrue((skills / "git-workflow").is_symlink())
        commands = sorted(
            p.name for p in (self.root / ".opencode" / "commands").iterdir()
        )
        self.assertEqual(commands, [f"keystone-{c}.md" for c in COMMANDS])
        verify = (
            self.root / ".opencode" / "commands" / "keystone-verify.md"
        ).read_text()
        self.assertTrue(verify.startswith('---\ndescription: "'))
        self.assertIn("$ARGUMENTS", verify)
        self.assertIn(ROOT.as_posix() + "/scripts/verify.py", verify)
        self.assertNotIn("CLAUDE_PLUGIN_ROOT", verify)
        agent = (self.root / ".opencode" / "agents" / "code-reviewer.md").read_text()
        self.assertIn('mode: "subagent"', agent)

    def test_copilot_prompts_have_no_claude_placeholders(self):
        self.run_cli("copilot")
        prompts = list((self.root / ".github" / "prompts").glob("*.prompt.md"))
        self.assertEqual(len(prompts), len(COMMANDS))
        for prompt in prompts:
            text = prompt.read_text()
            self.assertNotIn("$ARGUMENTS", text)
            self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", text)
        agents = sorted(p.name for p in (self.root / ".github" / "agents").iterdir())
        self.assertEqual(agents, AGENTS)

    def test_cursor_gets_skills_only(self):
        self.run_cli("cursor")
        self.assertTrue(
            (self.root / ".agents" / "skills" / "agent-orchestration").exists()
        )
        self.assertFalse((self.root / ".cursor").exists())
        self.assertFalse((self.root / ".opencode").exists())

    def test_reinstall_is_idempotent_and_users_files_are_kept(self):
        mine = self.root / ".agents" / "skills" / "git-workflow"
        mine.mkdir(parents=True)
        (mine / "SKILL.md").write_text("my own skill")
        out = self.run_cli("opencode")
        self.assertIn("kept yours", out)
        self.run_cli("opencode")
        self.assertEqual((mine / "SKILL.md").read_text(), "my own skill")
        self.run_cli("opencode", "--uninstall")
        self.assertEqual(
            sorted(p.name for p in (self.root / ".agents" / "skills").iterdir()),
            ["git-workflow"],
        )
        self.assertEqual(list((self.root / ".opencode" / "commands").iterdir()), [])

    def test_copy_mode_marks_and_uninstalls_copies(self):
        self.run_cli("cursor", "--copy")
        copied = self.root / ".agents" / "skills" / "git-workflow"
        self.assertFalse(copied.is_symlink())
        self.assertTrue((copied / ia.COPY_MARKER).exists())
        self.run_cli("cursor", "--uninstall")
        self.assertFalse(copied.exists())

    def test_edited_copy_survives_reinstall_and_uninstall(self):
        self.run_cli("cursor", "--copy")
        skill = self.root / ".agents" / "skills" / "git-workflow"
        (skill / "SKILL.md").write_text("my edits")
        out = self.run_cli("cursor", "--copy")
        self.assertIn("edited since install", out)
        self.assertEqual((skill / "SKILL.md").read_text(), "my edits")
        self.run_cli("cursor", "--uninstall")
        self.assertEqual((skill / "SKILL.md").read_text(), "my edits")
        self.assertFalse(
            (self.root / ".agents" / "skills" / "testing-strategy").exists()
        )

    def test_file_added_to_a_copy_is_never_deleted(self):
        self.run_cli("cursor", "--copy")
        notes = self.root / ".agents" / "skills" / "git-workflow" / "OUR-NOTES.md"
        notes.write_text("team notes")
        self.run_cli("cursor", "--copy")
        self.run_cli("cursor", "--uninstall")
        self.assertEqual(notes.read_text(), "team notes")

    def test_edited_generated_command_is_kept(self):
        self.run_cli("opencode")
        command = self.root / ".opencode" / "commands" / "keystone-review.md"
        command.write_text(command.read_text() + "\nOur review rule.\n")
        edited = command.read_text()
        self.assertIn("edited since install", self.run_cli("opencode"))
        self.run_cli("opencode", "--uninstall")
        self.assertEqual(command.read_text(), edited)
        self.assertFalse(
            (self.root / ".opencode" / "commands" / "keystone-plan.md").exists()
        )

    def test_links_to_a_missing_or_other_checkout_are_reported_not_touched(self):
        skills = self.root / ".agents" / "skills"
        skills.mkdir(parents=True)
        gone = self.root / "old-clone" / "skills" / "git-workflow"
        fork = self.root / "fork" / "skills" / "testing-strategy"
        fork.mkdir(parents=True)
        (self.root / "fork" / ".claude-plugin").mkdir()
        (self.root / "fork" / ".claude-plugin" / "plugin.json").write_text(
            '{"name": "keystone"}'
        )
        (skills / "git-workflow").symlink_to(gone, target_is_directory=True)
        (skills / "testing-strategy").symlink_to(fork, target_is_directory=True)
        out = self.run_cli("cursor")
        self.assertEqual(out.count("missing or different Keystone checkout"), 2)
        self.assertEqual(os.readlink(skills / "git-workflow"), str(gone))
        self.assertEqual(os.readlink(skills / "testing-strategy"), str(fork))
        out = self.run_cli("cursor", "--uninstall")
        self.assertEqual(out.count("missing or different Keystone checkout"), 2)
        self.assertEqual(
            sorted(p.name for p in skills.iterdir()),
            ["git-workflow", "testing-strategy"],
        )

    def test_unreadable_copy_is_kept_and_the_run_completes(self):
        self.run_cli("cursor", "--copy")
        real = Path.read_bytes

        def read_bytes(path):
            if path.name == "SKILL.md" and path.parent.name == "git-workflow":
                raise PermissionError("unreadable")
            return real(path)

        with mock.patch.object(Path, "read_bytes", read_bytes):
            out = self.run_cli("cursor", "--uninstall")
        self.assertIn("edited since install", out)
        skills = self.root / ".agents" / "skills"
        self.assertEqual([p.name for p in skills.iterdir()], ["git-workflow"])

    def test_users_own_link_is_kept(self):
        mine = self.root / "my-skills" / "skills" / "git-workflow"
        mine.mkdir(parents=True)
        (mine / "SKILL.md").write_text("mine")
        link = self.root / ".agents" / "skills" / "git-workflow"
        link.parent.mkdir(parents=True)
        link.symlink_to(mine, target_is_directory=True)
        self.assertIn("kept yours", self.run_cli("cursor"))
        self.run_cli("cursor", "--uninstall")
        self.assertTrue(link.is_symlink())
        self.assertEqual((link / "SKILL.md").read_text(), "mine")

    def test_copilot_files_carry_input_variable_and_agent_fields(self):
        self.run_cli("copilot")
        verify = (
            self.root / ".github" / "prompts" / "keystone-verify.prompt.md"
        ).read_text()
        self.assertIn('verify.py" ${input:args}', verify)
        agent = (self.root / ".github" / "agents" / "code-reviewer.md").read_text()
        self.assertTrue(agent.startswith('---\nname: "code-reviewer"\ndescription: "'))
        self.assertIn("\n# Code Reviewer", agent)

    def test_dry_run_writes_nothing_and_contract_is_added_only_when_absent(self):
        self.run_cli("copilot", "--dry-run", "--contract")
        self.assertEqual(list(self.root.iterdir()), [])
        self.run_cli("cursor", "--contract")
        self.assertEqual(
            (self.root / "AGENTS.md").read_text(), (ROOT / "AGENTS.md").read_text()
        )
        (self.root / "AGENTS.md").write_text("team rules")
        self.assertIn("merge", self.run_cli("cursor", "--contract"))
        self.assertEqual((self.root / "AGENTS.md").read_text(), "team rules")


if __name__ == "__main__":
    unittest.main()
