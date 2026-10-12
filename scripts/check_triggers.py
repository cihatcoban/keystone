#!/usr/bin/env python3
"""Static routing check — no model calls, runs in CI.

Routing happens on the `description` field alone. For each eval case:

  POSITIVE  the prompt must share meaningful vocabulary with its own skill's
            description, otherwise the skill is unlikely to be selected.
  NEGATIVE  the prompt must NOT match this skill better than it matches the
            skill that should own it — a cheap collision detector.

Scoring is deliberately crude (stemmed token overlap). It catches the common
failure — a trigger phrase nobody put in the description — without pretending
to model the router.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STOP = set(
    """a an and are as at be by can do does for from how i if in into is it
its me my not of on or our should so that the then there these this to us we what
when where which who why will with you your use used using need needs""".split()
)


def stem(w: str) -> str:
    for suf in ("ing", "ed", "es", "s"):
        if len(w) > 5 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def tokens(s: str) -> set[str]:
    return {
        stem(w)
        for w in re.findall(r"[a-zA-Z][\w-]+", s.lower())
        if len(w) > 2 and w not in STOP
    }


def descriptions() -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for f in sorted((ROOT / "skills").glob("*/SKILL.md")):
        m = re.search(r"^description:\s*(.+)$", f.read_text(encoding="utf-8"), re.M)
        out[f.parent.name] = tokens(m.group(1)) if m else set()
    return out


def main() -> int:
    desc = descriptions()
    weak = 0
    collisions = 0
    total = 0

    for case_file in sorted((ROOT / "evals" / "cases").glob("*.json")):
        case = json.loads(case_file.read_text(encoding="utf-8"))
        name = case["skill_name"]
        own = desc.get(name, set())

        for p in case["trigger"]["positive"]:
            total += 1
            shared = tokens(p["prompt"]) & own
            if not shared:
                weak += 1
                print(f"WEAK      {name}: no shared vocabulary with '{p['prompt']}'")

        for n in case["trigger"]["negative"]:
            t = tokens(n["prompt"])
            mine = len(t & own)
            best = max(
                ((len(t & d), s) for s, d in desc.items() if s != name),
                default=(0, "-"),
            )
            if mine and mine >= best[0]:
                collisions += 1
                print(
                    f"COLLISION {name}: negative prompt '{n['prompt']}' "
                    f"matches it ({mine}) >= best other {best[1]} ({best[0]})"
                )

    print(f"\n{total} positive prompts · {weak} weak · {collisions} collisions")
    return 1 if (weak or collisions) else 0


if __name__ == "__main__":
    sys.exit(main())
