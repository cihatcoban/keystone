"""Tests for scripts/validate_repo.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import validate_repo as vr  # noqa: E402 — must follow the sys.path insert; scripts/ is not a package

BODY = "# Example\n\n" + "word " * 400 + "\n\n## Exit checklist\n\n- [ ] done\n"


def description(length: int) -> str:
    head = "Does one thing well. Triggers - "
    return head + "x" * (length - len(head))


class DescriptionTargetTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        vr.errors.clear()
        vr.warnings.clear()

    def tearDown(self) -> None:
        self._tmp.cleanup()
        vr.errors.clear()
        vr.warnings.clear()

    def skill(self, desc: str) -> None:
        d = self.base / "skills" / "example-skill"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            f"---\nname: example-skill\ndescription: {desc}\n---\n{BODY}",
            encoding="utf-8",
        )

    def desc_findings(self) -> list[str]:
        return [m for m in vr.errors + vr.warnings if "description" in m]

    def test_at_target_is_clean(self) -> None:
        self.skill(description(vr.DESC_TARGET))
        vr.check_skills(self.base)
        self.assertEqual(self.desc_findings(), [])

    def test_over_target_warns_without_failing(self) -> None:
        self.skill(description(vr.DESC_TARGET + 1))
        vr.check_skills(self.base)
        self.assertEqual([m for m in vr.errors if "description" in m], [])
        self.assertTrue(any(f"target {vr.DESC_TARGET}" in m for m in vr.warnings))

    def test_over_hard_limit_still_errors(self) -> None:
        self.skill(description(vr.DESC_MAX + 1))
        vr.check_skills(self.base)
        self.assertTrue(any(f"{vr.DESC_MIN}-{vr.DESC_MAX}" in m for m in vr.errors))


if __name__ == "__main__":
    unittest.main()
