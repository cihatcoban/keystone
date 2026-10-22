"""Tests for the hook layer's infrastructure: config, dialects, dispatch, events."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "hooks"))
sys.path.insert(0, str(ROOT / "scripts"))

from keystone_hooks import core, dispatch, events  # noqa: E402 — must follow the sys.path insert; hooks/ is not a package

import build_adapters as ba  # noqa: E402 — must follow the sys.path insert; scripts/ is not a package
import install_hooks  # noqa: E402 — must follow the sys.path insert; scripts/ is not a package


class ConfigTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write_config(self, data: dict) -> None:
        (self.root / ".keystone").mkdir()
        (self.root / ".keystone" / "config.json").write_text(json.dumps(data))

    def test_defaults_to_warn(self):
        cfg = core.load_config(self.root, env={})
        self.assertEqual(cfg.profile, "warn")
        self.assertIn("main", cfg.protected_branches)

    def test_environment_overrides_file(self):
        self.write_config({"profile": "strict", "disabled_hooks": ["bar.suppression"]})
        cfg = core.load_config(
            self.root,
            env={
                "KEYSTONE_HOOK_PROFILE": "OFF",
                "KEYSTONE_DISABLED_HOOKS": "git.*, secret",
            },
        )
        self.assertEqual(cfg.profile, "off")
        self.assertEqual(cfg.disabled, ["bar.suppression", "git.*", "secret"])

    def test_unknown_profile_falls_back_with_a_note(self):
        cfg = core.load_config(self.root, env={"KEYSTONE_HOOK_PROFILE": "paranoid"})
        self.assertEqual(cfg.profile, "warn")
        self.assertTrue(cfg.notes)

    def test_broken_config_file_is_ignored_with_a_note(self):
        (self.root / ".keystone").mkdir()
        (self.root / ".keystone" / "config.json").write_text("{not json")
        cfg = core.load_config(self.root, env={})
        self.assertEqual(cfg.profile, "warn")
        self.assertTrue(cfg.notes)

    def test_disable_by_id_family_and_glob(self):
        cfg = core.Config(disabled=["git.force-push", "secret", "bar.*"])
        self.assertTrue(cfg.is_disabled("git.force-push"))
        self.assertFalse(cfg.is_disabled("git.no-verify"))
        self.assertTrue(cfg.is_disabled("secret.write"))
        self.assertTrue(cfg.is_disabled("bar.suppression"))
        self.assertTrue(
            core.Config(disabled=["rules.project"]).is_disabled("rules.project/no-x")
        )


class DialectTest(unittest.TestCase):
    def test_pre_tool_block_per_harness(self):
        claude = core.render("claude-code", "shell", "block", "no")
        self.assertEqual(claude["hookSpecificOutput"]["permissionDecision"], "deny")
        gemini = core.render("gemini", "edit", "block", "no")
        self.assertEqual(gemini, {"decision": "deny", "reason": "no"})

    def test_ask_is_native_where_supported(self):
        claude = core.render("claude-code", "shell", "ask", "sure?")
        self.assertEqual(claude["hookSpecificOutput"]["permissionDecision"], "ask")
        self.assertEqual(
            core.render("gemini", "shell", "ask", "sure?")["decision"], "ask"
        )

    def test_codex_never_receives_ask(self):
        self.assertEqual(core.adapt_to_harness("ask", "codex", "warn"), "warn")
        self.assertEqual(core.adapt_to_harness("ask", "codex", "strict"), "block")
        self.assertEqual(core.adapt_to_harness("ask", "claude-code", "warn"), "ask")

    def test_warn_does_not_decide(self):
        out = core.render("claude-code", "edit", "warn", "careful")
        self.assertNotIn("permissionDecision", out["hookSpecificOutput"])
        self.assertEqual(out["systemMessage"], "careful")

    def test_stop_block_per_harness(self):
        self.assertEqual(
            core.render("codex", "stop", "block", "x")["decision"], "block"
        )
        self.assertEqual(
            core.render("gemini", "stop", "block", "x")["decision"], "deny"
        )

    def test_session_start_context(self):
        out = core.render("gemini", "session-start", "context", "", "hello")
        self.assertEqual(out["hookSpecificOutput"]["additionalContext"], "hello")
        self.assertEqual(core.render("gemini", "session-start", "context", "", ""), {})


REGISTRY = {
    "triggers": {},
    "hooks": [
        {"id": "t.warns", "trigger": ["shell"], "warn": "warn", "strict": "block"},
        {"id": "t.blocks", "trigger": ["shell"], "warn": "block", "strict": "block"},
        {"id": "t.crashes", "trigger": ["shell"], "warn": "block", "strict": "block"},
        {"id": "t.stops", "trigger": ["stop"], "warn": "block", "strict": "block"},
    ],
}


def _crash(event, ctx):
    raise RuntimeError("boom")


GUARDS = {
    "t.warns": lambda e, c: [core.Finding("t.warns", "soft")],
    "t.blocks": lambda e, c: [core.Finding("t.blocks", "hard")],
    "t.crashes": _crash,
    "t.stops": lambda e, c: [core.Finding("t.stops", "verify first")],
}


class DispatchTest(unittest.TestCase):
    def run_hooks(self, trigger: str, raw: dict, env: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            raw = {"cwd": tmp, **raw}
            with (
                mock.patch.object(dispatch, "load_registry", return_value=REGISTRY),
                mock.patch.object(dispatch, "guards", return_value=GUARDS),
            ):
                return dispatch.run("claude-code", trigger, raw, env)

    def test_strongest_action_wins_and_crash_fails_open(self):
        out = self.run_hooks("shell", {"tool_input": {"command": "ls"}}, {})
        reason = out["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("[t.blocks]", reason)
        self.assertIn("[t.warns]", reason)
        self.assertIn("KEYSTONE_DISABLED_HOOKS=", reason)

    def test_disabled_hook_is_skipped(self):
        out = self.run_hooks("shell", {}, {"KEYSTONE_DISABLED_HOOKS": "t.blocks"})
        self.assertNotIn("permissionDecision", out["hookSpecificOutput"])
        self.assertIn("[t.warns]", out["systemMessage"])
        self.assertNotIn("[t.blocks]", out["systemMessage"])

    def test_off_profile_runs_nothing(self):
        self.assertEqual(
            self.run_hooks("shell", {}, {"KEYSTONE_HOOK_PROFILE": "off"}), {}
        )

    def test_stop_does_not_loop(self):
        first = self.run_hooks("stop", {}, {})
        self.assertEqual(first["decision"], "block")
        again = self.run_hooks("stop", {"stop_hook_active": True}, {})
        self.assertNotIn("decision", again)
        self.assertIn("verify first", again["systemMessage"])


class CliTest(unittest.TestCase):
    def call(self, stdin: str, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["sh", str(ROOT / "hooks" / "run.sh"), *args],
            input=stdin,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_garbage_input_exits_zero_silently(self):
        proc = self.call("{not json", "--harness", "codex", "--trigger", "shell")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")

    def test_output_is_one_json_object_or_nothing(self):
        raw = json.dumps({"cwd": str(ROOT), "tool_input": {"command": "ls"}})
        proc = self.call(raw, "--harness", "claude-code", "--trigger", "shell")
        self.assertEqual(proc.returncode, 0)
        if proc.stdout.strip():
            self.assertIsInstance(json.loads(proc.stdout), dict)


class EventsTest(unittest.TestCase):
    def test_segments_respect_quotes_and_operators(self):
        segs = events.segments('FOO=1 git commit -m "a | b; c" && rm -rf build # note')
        self.assertEqual([s.argv[0] for s in segs], ["git", "rm"])
        self.assertEqual(segs[0].env, {"FOO": "1"})
        self.assertEqual(segs[0].argv[3], "a | b; c")

    def test_git_args_skip_global_options(self):
        seg = events.segments("git -C repo -c core.hooksPath=/dev/null push -f")[0]
        self.assertEqual(
            events.git_args(seg), ("push", ["-f"], ["core.hooksPath=/dev/null"])
        )
        self.assertIsNone(events.git_args(events.segments("ls -la")[0]))

    def test_apply_patch_parsing(self):
        patch = (
            "*** Begin Patch\n*** Add File: a.txt\n+hello\n*** Update File: b.py\n"
            "@@\n-old\n+new\n*** Delete File: c.py\n*** End Patch"
        )
        self.assertEqual(
            events.parse_apply_patch(patch),
            [
                ("Add", "a.txt", "", "hello"),
                ("Update", "b.py", "old", "new"),
                ("Delete", "c.py", "", ""),
            ],
        )

    def test_normalize_each_harness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            (root / "f.txt").write_text("one\ntwo\n")
            claude = events.normalize(
                "claude-code",
                "edit",
                {
                    "cwd": tmp,
                    "tool_name": "Write",
                    "tool_input": {
                        "file_path": str(root / "f.txt"),
                        "content": "one\nthree\n",
                    },
                },
            )
            change = claude.changes[0]
            self.assertEqual((change.path, change.whole_file), ("f.txt", True))
            self.assertEqual(change.added_lines(), ["three"])
            self.assertEqual(change.removed_lines(), ["two"])
            multi = events.normalize(
                "claude-code",
                "edit",
                {
                    "cwd": tmp,
                    "tool_name": "MultiEdit",
                    "tool_input": {
                        "file_path": "f.txt",
                        "edits": [{"old_string": "a", "new_string": "b"}] * 2,
                    },
                },
            )
            self.assertEqual(len(multi.changes), 2)
            codex = events.normalize(
                "codex",
                "edit",
                {
                    "cwd": tmp,
                    "tool_name": "apply_patch",
                    "tool_input": {
                        "command": "*** Begin Patch\n*** Delete File: f.txt\n*** End Patch"
                    },
                },
            )
            self.assertTrue(codex.changes[0].deleted)
            self.assertEqual(codex.changes[0].before, "one\ntwo\n")
            gemini = events.normalize(
                "gemini",
                "shell",
                {
                    "cwd": tmp,
                    "tool_name": "run_shell_command",
                    "tool_input": {"command": "ls"},
                },
            )
            self.assertEqual(gemini.command, "ls")
            listed = events.normalize(
                "codex",
                "shell",
                {"cwd": tmp, "tool_input": {"command": ["bash", "-lc", "git status"]}},
            )
            self.assertEqual(listed.command, "git status")


class ManifestTest(unittest.TestCase):
    REG = {
        "triggers": {
            "shell": {
                "timeout_s": 7,
                "claude-code": {"event": "PreToolUse", "matcher": "Bash"},
                "codex": {"event": "PreToolUse", "matcher": "^Bash$"},
                "gemini": {"event": "BeforeTool", "matcher": "^run_shell_command$"},
            },
            "stop": {
                "timeout_s": 30,
                "claude-code": {"event": "Stop"},
                "codex": {"event": "Stop"},
                "gemini": {"event": "AfterAgent"},
            },
        },
        "hooks": [{"id": "x.y", "trigger": ["shell"]}],
    }

    def test_only_used_triggers_and_native_units(self):
        claude = json.loads(ba.render_hook_manifest("claude-code", self.REG))
        self.assertEqual(list(claude["hooks"]), ["PreToolUse"])
        handler = claude["hooks"]["PreToolUse"][0]["hooks"][0]
        self.assertEqual(handler["timeout"], 7)
        self.assertIn('"${CLAUDE_PLUGIN_ROOT}"/hooks/run.sh', handler["command"])
        gemini = json.loads(ba.render_hook_manifest("gemini", self.REG))
        handler = gemini["hooks"]["BeforeTool"][0]["hooks"][0]
        self.assertEqual(
            (handler["timeout"], handler["name"]), (7000, "keystone-shell")
        )
        codex = json.loads(ba.render_hook_manifest("codex", self.REG))
        self.assertIn(
            '"${PLUGIN_ROOT}"', codex["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        )

    def test_missing_harness_wiring_is_a_source_error(self):
        broken = json.loads(json.dumps(self.REG))
        del broken["triggers"]["shell"]["codex"]
        with self.assertRaises(ba.SourceError):
            ba.render_hook_manifest("codex", broken)


class InstallTest(unittest.TestCase):
    def test_install_is_idempotent_and_uninstall_keeps_user_hooks(self):
        mine = {
            "matcher": "Bash",
            "hooks": [{"type": "command", "command": "my-check"}],
        }
        settings = {"theme": "dark", "hooks": {"BeforeTool": [mine]}}
        events_ = {
            "BeforeTool": [
                {
                    "matcher": "x",
                    "hooks": [
                        {
                            "command": 'sh "/k/hooks/run.sh" --harness gemini --trigger shell'
                        }
                    ],
                }
            ]
        }
        once, _, added = install_hooks.merge(
            json.loads(json.dumps(settings)), events_, False
        )
        twice, removed, _ = install_hooks.merge(
            json.loads(json.dumps(once)), events_, False
        )
        self.assertEqual(once, twice)
        self.assertEqual((added, removed), (1, 1))
        clean, removed, _ = install_hooks.merge(twice, events_, True)
        self.assertEqual(clean, settings)
        self.assertEqual(removed, 1)

    def test_main_writes_backup_and_absolute_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / ".gemini" / "settings.json"
            target.parent.mkdir()
            target.write_text('{"theme": "dark"}')
            self.assertEqual(install_hooks.main(["gemini", "--root", tmp]), 0)
            self.assertTrue((target.parent / "settings.json.bak").exists())
            data = json.loads(target.read_text())
            self.assertEqual(data["theme"], "dark")
            commands = [
                h["command"]
                for g in data.get("hooks", {}).values()
                for x in g
                for h in x["hooks"]
            ]
            registry = ba.load_registry()
            used = {t for hook in registry["hooks"] for t in hook["trigger"]}
            self.assertEqual(len(commands), len(used))
            for command in commands:
                self.assertIn(ROOT.as_posix(), command)
                self.assertNotIn("${", command)

    def test_refuses_non_json_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / ".gemini" / "settings.json"
            target.parent.mkdir()
            target.write_text("// comment\n{}")
            self.assertEqual(install_hooks.main(["gemini", "--root", tmp]), 1)
            self.assertEqual(target.read_text(), "// comment\n{}")


if __name__ == "__main__":
    unittest.main()
