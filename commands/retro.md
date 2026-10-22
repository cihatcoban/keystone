---
description: Turn what a session learned into a reviewed lesson in LESSONS.md
---

Apply `context-engineering`; use `templates/LESSONS.template.md` for the shape.

Input: $ARGUMENTS (what went wrong or surprised you, if you know already)

1. List candidate lessons from this session: surprises, wrong assumptions,
   rework, a check that caught something late. Facts only, each with its
   evidence (commit, command output, PR).
2. Keep a candidate only if it should change how the next person works here.
   Drop one-off facts and personal preferences.
3. Prefer a mechanism to prose: if the lesson can become a test, a lint rule,
   a `CONSTRAINTS.md` row or a `.keystone/rules/` file, propose that instead
   and record it under "Enforced by".
4. Check `LESSONS.md` for an existing lesson on the same area; update it rather
   than adding a near-duplicate.
5. Show the proposed entries to the user. Add them to `LESSONS.md` only after
   they agree — lessons are reviewed like code, and an agent's unreviewed
   conclusion is not a lesson.
6. Report what was added, what became a check instead, and what was dropped.
