"""Tests for scripts/check_env.py.

Fake credentials are assembled at runtime so this file never contains a string
that matches a credential format — otherwise check_env would flag Keystone's
own test suite.
"""
from __future__ import annotations

import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import check_env  # noqa: E402 — must follow the sys.path insert; scripts/ is not a package

FAKE_OPENAI = "sk-proj-" + "A1b2C3d4" * 6
FAKE_AWS = "AKIA" + "ABCDEFGHIJKLMNOP"
FAKE_GOOGLE = "AIza" + "x" * 35


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


class Repo:
    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.email", "t@example.invalid")
        git(self.root, "config", "user.name", "t")

    def write(self, rel: str, content: str) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def track(self, *rels: str) -> None:
        git(self.root, "add", "-f", *rels)

    def codes(self) -> list[str]:
        return [f.code for f in check_env.check(self.root)]

    def output(self) -> str:
        buf = io.StringIO()
        with redirect_stdout(buf):
            for f in check_env.check(self.root):
                print(f.render())
        return buf.getvalue()

    def close(self) -> None:
        self._tmp.cleanup()


class CheckEnvTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Repo()
        self.repo.write(".gitignore", ".env\n.env.*\n!.env.example\n")
        self.repo.write(".env.example", "# key\nOPENAI_API_KEY=\nLOG_LEVEL=info\n")
        self.repo.track(".gitignore", ".env.example")

    def tearDown(self) -> None:
        self.repo.close()

    def test_clean_project_has_no_findings(self):
        self.assertEqual(self.repo.codes(), [])

    def test_tracked_env_file_is_an_error(self):
        self.repo.write(".env.production", "LOG_LEVEL=debug\n")
        self.repo.track(".env.production")
        self.assertIn("E1", self.repo.codes())

    def test_missing_gitignore_rule_is_an_error(self):
        self.repo.write(".gitignore", "node_modules/\n")
        self.assertIn("E2", self.repo.codes())

    def test_real_value_in_example_is_an_error_and_is_not_printed(self):
        self.repo.write(".env.example", f"OPENAI_API_KEY={FAKE_OPENAI}\n")
        self.assertIn("E3", self.repo.codes())
        self.assertNotIn(FAKE_OPENAI, self.repo.output())

    def test_secret_named_key_with_non_placeholder_value_is_an_error(self):
        self.repo.write(".env.example", "DB_PASSWORD=hunter2\n")
        self.assertIn("E3", self.repo.codes())

    def test_placeholders_are_allowed(self):
        self.repo.write(".env.example", "API_KEY=<your-key>\nTOKEN=changeme\nSECRET=\n")
        self.assertNotIn("E3", self.repo.codes())

    def test_credential_in_tracked_source_is_an_error_and_is_not_printed(self):
        self.repo.write("src/app.py", f'key = "{FAKE_AWS}"\n')
        self.repo.track("src/app.py")
        self.assertIn("E4", self.repo.codes())
        self.assertNotIn(FAKE_AWS, self.repo.output())
        self.assertIn("src/app.py:1", self.repo.output())

    def test_allow_marker_suppresses_a_reviewed_line(self):
        self.repo.write("docs/x.md", f"{FAKE_GOOGLE}  <!-- keystone:allow-secret revoked sample -->\n")
        self.repo.track("docs/x.md")
        self.assertNotIn("E4", self.repo.codes())

    def test_local_env_drift_is_a_warning_and_values_are_not_printed(self):
        self.repo.write(".env", "OPENAI_API_KEY=x\nUNDOCUMENTED=supersecretvalue\n")
        self.assertIn("W1", self.repo.codes())
        self.assertNotIn("supersecretvalue", self.repo.output())

    def test_variable_read_by_code_but_undocumented_is_a_warning(self):
        self.repo.write("src/settings.py", 'import os\nX = os.environ["PAYMENT_URL"]\n')
        self.assertIn("W2", self.repo.codes())

    def test_documented_variables_read_by_code_are_fine(self):
        self.repo.write("src/settings.py", 'import os\nX = os.getenv("OPENAI_API_KEY")\n')
        self.assertNotIn("W2", self.repo.codes())

    def test_reads_in_several_languages_are_detected(self):
        self.repo.write("a.js", "const a = process.env.JS_VAR;\n")
        self.repo.write("B.java", 'String b = System.getenv("JAVA_VAR");\n')
        self.repo.write("c.go", 'c := os.Getenv("GO_VAR")\n')
        out = self.repo.output()
        for name in ("JS_VAR", "JAVA_VAR", "GO_VAR"):
            self.assertIn(name, out)

    def test_test_code_is_excluded_from_drift_but_not_from_secret_scan(self):
        self.repo.write("tests/test_settings.py", 'os.environ["FIXTURE_ONLY"] = "1"\n')
        self.repo.write("src/app_test.go", 'os.Getenv("GO_FIXTURE")\n')
        self.assertNotIn("W2", self.repo.codes())
        self.repo.write("tests/test_client.py", f'TOKEN = "{FAKE_AWS}"\n')
        self.repo.track("tests/test_client.py")
        self.assertIn("E4", self.repo.codes())

    def test_no_example_file_while_code_reads_env_is_a_warning(self):
        (self.repo.root / ".env.example").unlink()
        git(self.repo.root, "rm", "-q", "--cached", ".env.example")
        self.repo.write("src/settings.py", 'import os\nX = os.environ["A_VAR"]\n')
        self.assertIn("W3", self.repo.codes())

    def test_exit_code_strict_mode(self):
        self.repo.write("src/settings.py", 'import os\nX = os.environ["A_VAR"]\n')
        script = Path(check_env.__file__)
        lenient = subprocess.run([sys.executable, script, "--root", self.repo.root], capture_output=True)
        strict = subprocess.run([sys.executable, script, "--root", self.repo.root, "--strict"],
                                capture_output=True)
        self.assertEqual(lenient.returncode, 0)
        self.assertEqual(strict.returncode, 1)


if __name__ == "__main__":
    unittest.main()
