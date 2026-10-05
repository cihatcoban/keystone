---
description: Implement the next task in thin slices, test first
---

Apply `incremental-delivery` and `test-driven-development` together.

Input: $ARGUMENTS (task id, or the first open task in the plan)

Per slice: failing test observed red → minimal code → green → clean up → full
suite → one commit.

- Keep structural and behavioral changes in separate commits.
- Hide incomplete behavior behind a flag defaulting to off.
- Log anything out of scope as an issue; do not fix it here.
- Stop and report on: irreversible steps, a slice several times larger than
  planned, no way to test, or a `CONSTRAINTS.md` threshold in the way.

With `auto`: continue through the plan's tasks in order under the same rules,
pausing on any stop condition.
