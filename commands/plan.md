---
description: Break an approved spec into ordered, verifiable, vertically sliced tasks
---

Apply `planning-and-task-breakdown`.

Input: $ARGUMENTS (spec path or topic)

1. No spec? Run `/spec` first.
2. Slice vertically — each task crosses layers and produces observable behavior.
3. Put the highest-uncertainty task first; contracts before consumers.
4. Size S/M/L; split every L until none remain.
5. Include tasks for flag removal and cleanup.
6. Write `docs/plans/NNN-<slug>.md` and register the tasks in the task list.
