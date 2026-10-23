---
description: Break an approved spec into ordered, verifiable, vertically sliced tasks
---

Apply `planning-and-task-breakdown`.

Input: $ARGUMENTS (spec path or topic)

1. No spec? Run `/spec` first.
2. Slice vertically — each task crosses layers and produces observable behavior.
3. Put the highest-uncertainty task first; contracts before consumers.
4. Size S/M/L; split every L until none remain.
5. Give every task its files and a brief a cold reader can act on; mark
   `Parallel with:` only for tasks that share no files and no outputs.
6. Include tasks for flag removal and cleanup.
7. Write `docs/plans/NNN-<slug>.md` from `templates/plan.template.md` and
   register the tasks in the task list.
8. More than five tasks, parallel work or an irreversible step: have
   `adversarial-reviewer` check the plan against the spec before T1.
