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


class DocPointerTest(unittest.TestCase):
    """Backticked `references/…` and `templates/…` paths must exist (check 11)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        for sub in ("skills/example-skill", "references", "templates", "agents"):
            (self.base / sub).mkdir(parents=True)
        (self.base / "references" / "real.md").write_text("# Real\n", encoding="utf-8")
        (self.base / "templates" / "plan.template.md").write_text(
            "# P\n", encoding="utf-8"
        )
        vr.errors.clear()
        vr.warnings.clear()

    def tearDown(self) -> None:
        self._tmp.cleanup()
        vr.errors.clear()
        vr.warnings.clear()

    def write(self, rel: str, text: str) -> None:
        (self.base / rel).write_text(text, encoding="utf-8")

    def test_existing_pointers_are_clean(self) -> None:
        self.write(
            "skills/example-skill/SKILL.md",
            "See `references/real.md` and `templates/plan.template.md`.\n",
        )
        vr.check_doc_pointers(self.base)
        self.assertEqual(vr.errors, [])

    def test_missing_reference_from_a_skill_errors(self) -> None:
        self.write("skills/example-skill/SKILL.md", "See `references/gone.md`.\n")
        vr.check_doc_pointers(self.base)
        self.assertEqual(len(vr.errors), 1)
        self.assertIn("references/gone.md", vr.errors[0])
        self.assertIn("skills/example-skill/SKILL.md", vr.errors[0])

    def test_missing_template_from_a_reference_errors(self) -> None:
        self.write("references/real.md", "Fill `templates/nope.template.md`.\n")
        vr.check_doc_pointers(self.base)
        self.assertEqual(len(vr.errors), 1)
        self.assertIn("templates/nope.template.md", vr.errors[0])

    def test_agents_are_checked_too(self) -> None:
        self.write("agents/reviewer.md", "Lens: `references/lenses.md`.\n")
        vr.check_doc_pointers(self.base)
        self.assertEqual(len(vr.errors), 1)


class SkillCountClaimTest(unittest.TestCase):
    """Manifests and docs must state the real number of skills."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        (self.base / ".claude-plugin").mkdir()
        (self.base / "docs").mkdir()
        vr.errors.clear()
        vr.warnings.clear()

    def tearDown(self) -> None:
        self._tmp.cleanup()
        vr.errors.clear()
        vr.warnings.clear()

    def write(self, rel: str, text: str) -> None:
        (self.base / rel).write_text(text, encoding="utf-8")

    def test_matching_counts_are_clean(self) -> None:
        self.write(
            ".claude-plugin/marketplace.json", '{"d": "34 stack-agnostic skills"}'
        )
        self.write("README.md", "Adopting 34 skills at once.\n")
        vr.check_count_claims(self.base, 34)
        self.assertEqual(vr.errors, [])

    def test_stale_count_in_a_manifest_errors(self) -> None:
        self.write(
            ".claude-plugin/marketplace.json", '{"d": "32 stack-agnostic skills"}'
        )
        vr.check_count_claims(self.base, 34)
        self.assertEqual(len(vr.errors), 1)
        self.assertIn("32", vr.errors[0])
        self.assertIn("marketplace.json", vr.errors[0])

    def test_other_projects_counts_are_ignored(self) -> None:
        self.write("docs/compare.md", "everything-claude-code ships 311 skills.\n")
        vr.check_count_claims(self.base, 34)
        self.assertEqual(vr.errors, [])


if __name__ == "__main__":
    unittest.main()
