"""True- and false-positive cases for every WP1 guard.

Credential-shaped strings are assembled at runtime so that gitleaks and
check_env.py, which scan this repository, never see a literal one.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "hooks"))

from keystone_hooks import (  # noqa: E402 — must follow the sys.path insert; hooks/ is not a package
    core,
    dispatch,
    events,
    guards_bar,
    guards_git,
    guards_irreversible,
    guards_rules,
    guards_secret,
)

AWS_KEY = "AK" + "IA" + "QWERTYUIOPASDFGH"
GENERIC = "api_key = " + '"' + "Zq8" + "Lm2Vx9Rt4Ks7Wp1Yb6Nc3" + '"'

CONSTRAINTS = """# CONSTRAINTS.md

## 1. Correctness

| Dimension | Threshold | Measured by | Current |
|---|---|---|---|
| Line coverage | ≥ 80% | `pytest --cov` | 85% |
| Lint errors | 0 errors | `ruff check` | 0 |
| Catalog size | ≤ 3,800 tokens | `make validate` | 2,808 |
"""


class Repo:
    """A throwaway git repository with optional CONSTRAINTS.md."""

    def __init__(self, constraints: str = CONSTRAINTS, branch: str = "main") -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.git("init", "-q", "-b", branch)
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "t")
        if constraints:
            self.write("CONSTRAINTS.md", constraints)

    def git(self, *args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            capture_output=True,
            text=True,
            check=True,
        ).stdout

    def write(self, rel: str, text: str) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def ctx(self, **config) -> dict:
        cfg = core.Config(**config)
        return {
            "config": cfg,
            "profile": cfg.profile,
            "constraints_text": (self.root / "CONSTRAINTS.md").read_text()
            if (self.root / "CONSTRAINTS.md").exists()
            else "",
        }

    def shell(self, command: str) -> events.Event:
        raw = {"cwd": str(self.root), "tool_input": {"command": command}}
        return events.normalize("claude-code", "shell", raw, self.root)

    def edit(self, path: str, old: str, new: str) -> events.Event:
        raw = {
            "cwd": str(self.root),
            "tool_name": "Edit",
            "tool_input": {"file_path": path, "old_string": old, "new_string": new},
        }
        return events.normalize("claude-code", "edit", raw, self.root)

    def write_tool(self, path: str, content: str) -> events.Event:
        raw = {
            "cwd": str(self.root),
            "tool_name": "Write",
            "tool_input": {"file_path": path, "content": content},
        }
        return events.normalize("claude-code", "edit", raw, self.root)

    def close(self) -> None:
        self._tmp.cleanup()


class GuardCase(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Repo()

    def tearDown(self) -> None:
        self.repo.close()

    def ids(self, guard, event, **config) -> list[str]:
        return [f.hook_id for f in guard(event, self.repo.ctx(**config))]


class ConstraintsLoweredTest(GuardCase):
    def test_lowered_minimum_fires(self):
        e = self.repo.edit(
            "CONSTRAINTS.md",
            "| Line coverage | ≥ 80% | `pytest --cov` | 85% |",
            "| Line coverage | ≥ 70% | `pytest --cov` | 85% |",
        )
        self.assertEqual(
            self.ids(guards_bar.constraints_lowered, e), ["bar.constraints-lowered"]
        )

    def test_raised_count_and_ceiling_fire(self):
        e = self.repo.edit(
            "CONSTRAINTS.md",
            "| Lint errors | 0 errors | `ruff check` | 0 |",
            "| Lint errors | 5 errors | `ruff check` | 0 |",
        )
        self.assertTrue(self.ids(guards_bar.constraints_lowered, e))
        e = self.repo.edit(
            "CONSTRAINTS.md",
            "| Catalog size | ≤ 3,800 tokens | `make validate` | 2,808 |",
            "| Catalog size | ≤ 4,500 tokens | `make validate` | 2,808 |",
        )
        self.assertTrue(self.ids(guards_bar.constraints_lowered, e))

    def test_removed_row_in_full_write_fires(self):
        content = CONSTRAINTS.replace(
            "| Lint errors | 0 errors | `ruff check` | 0 |\n", ""
        )
        e = self.repo.write_tool("CONSTRAINTS.md", content)
        self.assertTrue(self.ids(guards_bar.constraints_lowered, e))

    def test_tightening_and_current_column_do_not_fire(self):
        e = self.repo.edit(
            "CONSTRAINTS.md",
            "| Line coverage | ≥ 80% | `pytest --cov` | 85% |",
            "| Line coverage | ≥ 90% | `pytest --cov` | 91% |",
        )
        self.assertEqual(self.ids(guards_bar.constraints_lowered, e), [])

    def test_other_files_are_ignored(self):
        e = self.repo.edit(
            "docs/notes.md", "| Line coverage | ≥ 80% |", "| Line coverage | ≥ 10% |"
        )
        self.assertEqual(self.ids(guards_bar.constraints_lowered, e), [])


class CheckConfigTest(GuardCase):
    def test_config_of_a_measured_tool_fires(self):
        self.repo.write("ruff.toml", "line-length = 88\n")
        e = self.repo.edit("ruff.toml", "line-length = 88", "line-length = 200")
        self.assertEqual(self.ids(guards_bar.check_config, e), ["bar.check-config"])

    def test_threshold_in_shared_manifest_fires(self):
        e = self.repo.edit(
            "pyproject.toml",
            "[tool.coverage.report]",
            "[tool.coverage.report]\nfail_under = 50",
        )
        self.assertTrue(self.ids(guards_bar.check_config, e))

    def test_protected_path_fires(self):
        e = self.repo.edit("config/lint/rules.yml", "a: 1", "a: 2")
        self.assertTrue(
            self.ids(guards_bar.check_config, e, protected_paths=["config/lint/*"])
        )

    def test_source_files_and_unrelated_settings_do_not_fire(self):
        self.assertEqual(
            self.ids(
                guards_bar.check_config,
                self.repo.edit("src/ruff_helper.py", "a = 1", "a = 2"),
            ),
            [],
        )
        self.assertEqual(
            self.ids(
                guards_bar.check_config,
                self.repo.edit(
                    "package.json", '"version": "1.0.0"', '"version": "1.0.1"'
                ),
            ),
            [],
        )

    def test_make_targets_protect_nothing(self):
        # `make validate` names a step, not a tool: validate.yml is not protected.
        e = self.repo.edit(".github/workflows/validate.yml", "a: 1", "a: 2")
        self.assertEqual(self.ids(guards_bar.check_config, e), [])


class SuppressionTest(GuardCase):
    def test_bare_suppression_fires(self):
        e = self.repo.edit("src/a.py", "import x", "import x  # noqa")
        self.assertEqual(self.ids(guards_bar.suppression, e), ["bar.suppression"])
        e = self.repo.edit("src/a.ts", "f()", "// @ts-ignore\nf()")
        self.assertTrue(self.ids(guards_bar.suppression, e))

    def test_justified_existing_or_documented_markers_do_not_fire(self):
        linked = "import x  # noqa: E402 — needs sys.path; https://example.com/issues/1"
        self.assertEqual(
            self.ids(
                guards_bar.suppression, self.repo.edit("src/a.py", "import x", linked)
            ),
            [],
        )
        kept = "import x  # noqa\nimport y"
        self.assertEqual(
            self.ids(
                guards_bar.suppression,
                self.repo.edit("src/a.py", "import x  # noqa", kept),
            ),
            [],
        )
        doc = self.repo.edit(
            "docs/lint.md", "", "Never add `eslint-disable` without a link."
        )
        self.assertEqual(self.ids(guards_bar.suppression, doc), [])


class TestWeakenedTest(GuardCase):
    def test_skip_focus_and_removal_fire(self):
        cases = [
            ("tests/test_a.py", "def test_a():", "@pytest.mark.skip\ndef test_a():"),
            ("src/a.test.ts", "it('works', () => {", "it.only('works', () => {"),
            (
                "tests/test_a.py",
                "def test_a():\n    assert f()\n\ndef test_b():\n    assert g()",
                "def test_a():\n    assert f()",
            ),
            (
                "tests/test_a.py",
                "    assert f() == 1\n    assert g() == 2",
                "    assert f() == 1",
            ),
        ]
        for path, old, new in cases:
            with self.subTest(path=path, new=new):
                self.assertEqual(
                    self.ids(guards_bar.test_weakened, self.repo.edit(path, old, new)),
                    ["bar.test-weakened"],
                )

    def test_removed_test_is_named_as_removed(self):
        e = self.repo.edit(
            "tests/test_a.py",
            "def test_a():\n    pass\n\ndef test_b():\n    pass",
            "def test_a():\n    pass",
        )
        [finding] = guards_bar.test_weakened(e, self.repo.ctx())
        self.assertIn("removes 1 test(s)", finding.message)

    def test_count_without_comparator_is_a_ceiling(self):
        # "0 errors" -> "5 errors" loosens; "85%" -> "70%" (no comparator) loosens too.
        e = self.repo.edit(
            "CONSTRAINTS.md",
            "| Line coverage | ≥ 80% | `pytest --cov` | 85% |",
            "| Line coverage | 80% | `pytest --cov` | 85% |",
        )
        self.assertEqual(self.ids(guards_bar.constraints_lowered, e), [])
        e = self.repo.edit(
            "CONSTRAINTS.md",
            "| Line coverage | 80% | `pytest --cov` | 85% |",
            "| Line coverage | 70% | `pytest --cov` | 85% |",
        )
        self.assertTrue(self.ids(guards_bar.constraints_lowered, e))

    def test_deleting_tests_from_the_shell_fires(self):
        for command in (
            "rm tests/test_a.py",
            "git rm -r tests",
            "cd x && rm -f src/a_test.go",
        ):
            with self.subTest(command=command):
                self.assertTrue(
                    self.ids(guards_bar.test_weakened, self.repo.shell(command))
                )

    def test_codex_patch_deleting_a_test_fires(self):
        raw = {
            "cwd": str(self.repo.root),
            "tool_name": "apply_patch",
            "tool_input": {
                "command": "*** Begin Patch\n*** Delete File: tests/test_a.py\n*** End Patch"
            },
        }
        e = events.normalize("codex", "edit", raw, self.repo.root)
        self.assertTrue(self.ids(guards_bar.test_weakened, e))

    def test_new_tests_source_code_and_build_cleanup_do_not_fire(self):
        added = self.repo.edit(
            "tests/test_a.py",
            "def test_a():\n    assert f()",
            "def test_a():\n    assert f()\n\ndef test_b():\n    assert g()",
        )
        self.assertEqual(self.ids(guards_bar.test_weakened, added), [])
        source = self.repo.edit("src/list.js", "items", "items.skip(1)")
        self.assertEqual(self.ids(guards_bar.test_weakened, source), [])
        self.assertEqual(
            self.ids(guards_bar.test_weakened, self.repo.shell("rm -rf build dist")), []
        )


class NoVerifyTest(GuardCase):
    def test_bypasses_fire(self):
        for command in (
            'git commit -m "x" --no-verify',
            "git commit -nm wip",
            "HUSKY=0 git push origin feature",
            "git -c core.hooksPath=/dev/null commit -m x",
            "git config core.hooksPath .nohooks",
        ):
            with self.subTest(command=command):
                self.assertEqual(
                    self.ids(guards_git.no_verify, self.repo.shell(command)),
                    ["git.no-verify"],
                )

    def test_lookalikes_do_not_fire(self):
        for command in (
            'git commit -m "-n"',
            "git push -n origin main",
            'echo "--no-verify"',
            "git log -n 5",
        ):
            with self.subTest(command=command):
                self.assertEqual(
                    self.ids(guards_git.no_verify, self.repo.shell(command)), []
                )


class ForcePushTest(GuardCase):
    def test_force_to_protected_fires(self):
        self.repo.write("a.txt", "a")
        self.repo.git("add", "a.txt")
        self.repo.git("commit", "-qm", "init")
        for command in (
            "git push --force origin main",
            "git push origin +main",
            "git push -f",  # current branch is main
            "git push origin :release/1.0",
            "git push --delete origin master",
        ):
            with self.subTest(command=command):
                self.assertEqual(
                    self.ids(guards_git.force_push, self.repo.shell(command)),
                    ["git.force-push"],
                )

    def test_normal_or_feature_pushes_do_not_fire(self):
        for command in (
            "git push origin main",
            "git push --force origin feature/x",
            "git push --force-with-lease origin my-branch",
            "git push -u origin feature",
        ):
            with self.subTest(command=command):
                self.assertEqual(
                    self.ids(guards_git.force_push, self.repo.shell(command)), []
                )

    def test_protected_branches_are_configurable(self):
        e = self.repo.shell("git push --force origin feature/x")
        self.assertTrue(
            self.ids(guards_git.force_push, e, protected_branches=["feature/*"])
        )


class SecretTest(GuardCase):
    def test_credentials_in_writes_fire(self):
        for content in (f"KEY = '{AWS_KEY}'\n", GENERIC + "\n"):
            with self.subTest(content=content[:12]):
                self.assertEqual(
                    self.ids(
                        guards_secret.secret_write,
                        self.repo.write_tool("src/c.py", content),
                    ),
                    ["secret.write"],
                )

    def test_placeholders_examples_and_allowed_lines_do_not_fire(self):
        placeholder = 'api_key = "your-api-key-goes-here"\n'
        low_entropy = 'password = "aaaaaaaaaaaaaaaaaaaaaaaa"\n'
        self.assertEqual(
            self.ids(
                guards_secret.secret_write,
                self.repo.write_tool("src/c.py", low_entropy),
            ),
            [],
        )
        self.assertEqual(
            self.ids(
                guards_secret.secret_write,
                self.repo.write_tool("src/c.py", placeholder),
            ),
            [],
        )
        example = self.repo.write_tool(".env.example", GENERIC + "\n")
        self.assertEqual(self.ids(guards_secret.secret_write, example), [])
        allowed = f"KEY = '{AWS_KEY}'  # keystone:allow-secret documented test vector\n"
        self.assertEqual(
            self.ids(
                guards_secret.secret_write, self.repo.write_tool("src/c.py", allowed)
            ),
            [],
        )

    def test_staged_credential_fires_on_commit_only(self):
        self.repo.write("c.py", f"KEY = '{AWS_KEY}'\n")
        self.repo.git("add", "c.py")
        self.assertEqual(
            self.ids(guards_secret.secret_staged, self.repo.shell('git commit -m "x"')),
            ["secret.staged"],
        )
        self.assertEqual(
            self.ids(guards_secret.secret_staged, self.repo.shell("git status")), []
        )

    def test_commit_all_includes_unstaged_tracked_changes(self):
        self.repo.write("c.py", "x = 1\n")
        self.repo.git("add", "c.py")
        self.repo.git("commit", "-qm", "init")
        self.repo.write("c.py", f"KEY = '{AWS_KEY}'\n")
        self.assertEqual(
            self.ids(guards_secret.secret_staged, self.repo.shell("git commit -m x")),
            [],
        )
        self.assertTrue(
            self.ids(guards_secret.secret_staged, self.repo.shell("git commit -am x"))
        )


class IrreversibleTest(GuardCase):
    def test_destructive_commands_fire(self):
        for command in (
            "rm -rf data",
            "rm -rf /",
            "git reset --hard HEAD~1",
            "git clean -fd",
            "git restore src/a.py",
            "psql -c 'DROP TABLE users'",
            "psql -c 'DELETE FROM users;'",
            "terraform destroy",
            "kubectl delete pod web-1",
            "npm publish",
            "cd app && rm -r uploads",
        ):
            with self.subTest(command=command):
                self.assertEqual(
                    self.ids(
                        guards_irreversible.irreversible, self.repo.shell(command)
                    ),
                    ["irreversible.command"],
                )

    def test_recoverable_commands_do_not_fire(self):
        for command in (
            "rm -rf node_modules build dist",
            "rm notes.txt",
            'echo "rm -rf /"',
            "git reset --soft HEAD~1",
            "git restore --staged a.py",
            "git checkout feature",
            "psql -c 'SELECT 1'",
            "psql -c 'DELETE FROM users WHERE id = 1'",
            "terraform plan",
            "npm install",
        ):
            with self.subTest(command=command):
                self.assertEqual(
                    self.ids(
                        guards_irreversible.irreversible, self.repo.shell(command)
                    ),
                    [],
                )


class CommitMessageTest(GuardCase):
    def history(self, subjects: list[str]) -> None:
        """Create commits in one `git fast-import` call (one process, not 2N)."""
        stream = "".join(
            f"commit refs/heads/main\ncommitter t <t@example.com> {1_700_000_000 + i} +0000\n"
            f"data {len(subject.encode())}\n{subject}\n"
            for i, subject in enumerate(subjects)
        )
        subprocess.run(
            ["git", "-C", str(self.repo.root), "fast-import", "--quiet"],
            input=stream,
            text=True,
            check=True,
            capture_output=True,
        )

    def fire(self, command: str, **config) -> list[str]:
        return [
            f.message
            for f in guards_git.commit_message_guard(
                self.repo.shell(command), self.repo.ctx(**config)
            )
        ]

    def test_detected_convention_is_enforced(self):
        self.history([f"feat(core): add part {i}" for i in range(6)])
        self.assertTrue(self.fire('git commit -m "updated stuff"'))
        self.assertTrue(self.fire('git commit -m "feat: add parser and fix lexer"'))
        self.assertTrue(self.fire('git commit -am "fix(api): Added retries."'))
        [message] = self.fire('git commit -m "wip"')
        self.assertIn("6 of the last 6 commits", message)

    def test_good_and_generated_messages_pass(self):
        self.history([f"fix(io): handle case {i}" for i in range(6)])
        for command in (
            'git commit -m "feat(hooks): add commit message guard" -m "Body explains why."',
            'git commit -m "docs: add tests and docs"',
            "git commit -m 'Revert \"feat: x\"'",
            "git commit --amend --no-edit",
            "git commit",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.fire(command), [])

    def test_no_convention_means_no_check(self):
        self.history(
            ["Initial import", "Tweak things", "More work", "Fix it", "Done", "Again"]
        )
        self.assertEqual(self.fire('git commit -m "whatever I like"'), [])
        self.assertTrue(
            self.fire(
                'git commit -m "whatever I like"', commit_convention="conventional"
            )
        )

    def test_commitlint_config_and_message_file(self):
        self.repo.write("commitlint.config.js", "module.exports = {}\n")
        self.repo.write("msg.txt", "feat: add thing\nno blank line\n")
        [message] = self.fire("git commit -F msg.txt")
        self.assertIn("commitlint", message)
        self.assertIn("blank line", message)

    def test_disabled_by_setting(self):
        self.history([f"feat: add part {i}" for i in range(6)])
        self.assertEqual(self.fire('git commit -m "wip"', commit_convention="none"), [])


RULE = """---
name: no-raw-sql
trigger: edit
pattern: \\bdb\\.raw\\(
paths: src/**, !src/db/**
action: block
---
Raw SQL bypasses the repository layer.
"""


class ProjectRulesTest(GuardCase):
    def test_matching_rule_fires_with_its_own_action(self):
        self.repo.write(".keystone/rules/no-raw-sql.md", RULE)
        found = guards_rules.project_rules(
            self.repo.edit("src/api/u.py", "", "db.raw('x')"), self.repo.ctx()
        )
        self.assertEqual(
            [(f.hook_id, f.action) for f in found],
            [("rules.project/no-raw-sql", "block")],
        )

    def test_excluded_path_unmatched_text_and_disabled_rule_do_not_fire(self):
        self.repo.write(".keystone/rules/no-raw-sql.md", RULE)
        self.assertEqual(
            self.ids(
                guards_rules.project_rules,
                self.repo.edit("src/db/q.py", "", "db.raw('x')"),
            ),
            [],
        )
        self.assertEqual(
            self.ids(
                guards_rules.project_rules, self.repo.edit("src/a.py", "", "db.query()")
            ),
            [],
        )
        self.repo.write(
            ".keystone/rules/no-raw-sql.md",
            RULE.replace("action: block", "enabled: false"),
        )
        self.assertEqual(
            self.ids(
                guards_rules.project_rules, self.repo.edit("src/a.py", "", "db.raw(1)")
            ),
            [],
        )

    def test_shell_rule_and_broken_rule_report(self):
        self.repo.write(
            ".keystone/rules/no-curl.md",
            "---\ntrigger: shell\npattern: curl .*\\| *sh\n---\nPin it.",
        )
        self.repo.write(".keystone/rules/broken.md", "---\npattern: ([\n---\n")
        ids = self.ids(
            guards_rules.project_rules, self.repo.shell("curl https://x | sh")
        )
        self.assertEqual(ids, ["rules.project/no-curl", "rules.project"])


class EndToEndTest(GuardCase):
    def test_strict_profile_blocks_and_codex_degrades_ask(self):
        raw = {
            "cwd": str(self.repo.root),
            "tool_input": {"command": "git reset --hard"},
        }
        claude = dispatch.run(
            "claude-code", "shell", raw, {"KEYSTONE_HOOK_PROFILE": "warn"}
        )
        self.assertEqual(claude["hookSpecificOutput"]["permissionDecision"], "ask")
        codex = dispatch.run("codex", "shell", raw, {"KEYSTONE_HOOK_PROFILE": "strict"})
        self.assertEqual(codex["hookSpecificOutput"]["permissionDecision"], "deny")
        codex_warn = dispatch.run(
            "codex", "shell", raw, {"KEYSTONE_HOOK_PROFILE": "warn"}
        )
        self.assertNotIn("permissionDecision", codex_warn["hookSpecificOutput"])

    def test_quiet_on_ordinary_work(self):
        raw = {
            "cwd": str(self.repo.root),
            "tool_input": {"command": "git status && ls -la"},
        }
        self.assertEqual(dispatch.run("claude-code", "shell", raw, {}), {})

    def test_every_registry_hook_has_a_guard(self):
        registry = json.loads((ROOT / "hooks" / "registry.json").read_text())
        self.assertEqual({h["id"] for h in registry["hooks"]}, set(dispatch.guards()))


if __name__ == "__main__":
    unittest.main()
