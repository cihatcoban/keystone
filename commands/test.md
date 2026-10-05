---
description: Design or repair the test suite — levels, data, flakiness, speed
---

Apply `testing-strategy`, with `test-driven-development` for new tests.

Input: $ARGUMENTS

1. Identify what risk is untested, not what code is uncovered.
2. Place each test at the cheapest level that could catch its defect.
3. Check the suite for: flakiness, shared mutable fixtures, sleeps, real clock,
   network in the fast tier, order dependence.
4. Report suite timings against the `CONSTRAINTS.md` budget.
5. Where confidence is unclear, run mutation testing on the core module and
   report the surviving mutants.
