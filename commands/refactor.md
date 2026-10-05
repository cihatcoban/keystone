---
description: Improve structure without changing behavior, safely
---

Apply `refactoring-and-simplification`.

Input: $ARGUMENTS

1. Confirm a safety net exists. No tests → write characterization tests that
   capture current behavior, including behavior that looks wrong.
2. No seam to test through → create one with the smallest possible edit and
   commit that alone.
3. Small steps, green and committed between each.
4. Never mix structural and behavioral change in one commit.
5. Remove only real duplication; leave coincidental similarity alone.
6. Report the complexity before and after, and confirm the tests are unchanged.
