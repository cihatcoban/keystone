#!/usr/bin/env python3
"""Scaffold a new skill from the template, with its eval case.

    python3 scripts/new_skill.py my-skill-name --category architect

Creates skills/<name>/SKILL.md and evals/cases/<name>.json, then tells you what
to fill in. Refuses to overwrite.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATEGORIES = ("meta", "define", "architect", "build", "verify", "operate")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("name", help="kebab-case skill name")
    ap.add_argument("--category", choices=CATEGORIES, default="build")
    args = ap.parse_args()

    name = args.name
    if not re.fullmatch(r"[a-z][a-z0-9]*(-[a-z0-9]+)*", name):
        print(f"error: '{name}' is not kebab-case")
        return 1

    sdir = ROOT / "skills" / name
    case = ROOT / "evals" / "cases" / f"{name}.json"
    if sdir.exists() or case.exists():
        print(f"error: {name} already exists")
        return 1

    template = (ROOT / "templates" / "SKILL.template.md").read_text(encoding="utf-8")
    body = template.replace("<kebab-case-name>", name)

    sdir.mkdir(parents=True)
    (sdir / "SKILL.md").write_text(body, encoding="utf-8")

    case.write_text(json.dumps({
        "skill_name": name,
        "trigger": {
            "positive": [{"prompt": "TODO: a phrase a person would actually type",
                          "top_k": 3} for _ in range(3)],
            "negative": [{"prompt": "TODO: a prompt another skill should own"}
                         for _ in range(2)],
        },
        "expectations": [
            f"'{name}' is selected among the top candidate skills",
            "The skill's exit checklist items are addressed in the response",
        ],
    }, indent=2) + "\n", encoding="utf-8")

    print(f"""created
  skills/{name}/SKILL.md
  evals/cases/{name}.json

next
  1. write the body first; the description last
  2. category '{args.category}' — add it to the router table in
     skills/using-skills/SKILL.md
  3. replace the TODO prompts with real ones
  4. make validate && python3 scripts/check_triggers.py""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
