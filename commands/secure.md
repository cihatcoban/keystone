---
description: Threat-model and harden a change
---

Apply `security-and-threat-modeling`.

Input: $ARGUMENTS

1. Trust boundaries and entry points for this change.
2. STRIDE prompts, answered in writing.
3. Check: input validation and bounds, parameterized queries, object-level
   authorization, secrets, error leakage, personal data.
4. Add negative authorization tests — user B must not reach user A's data.
5. Report findings with an exploitation scenario each; theoretical findings
   marked as such.
