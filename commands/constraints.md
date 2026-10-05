---
description: Establish the project quality bar as a written, enforceable contract
---

Apply `constraint-driven-development`.

1. Copy `templates/CONSTRAINTS.template.md` to the project root if absent.
2. Measure current values first — coverage, suite time, budget-relevant numbers.
3. Interview one dimension at a time; propose the documented default where the
   user has no number, and state what it costs and buys.
4. Where current is far from target, install a ratchet (diff-based gate) rather
   than an unreachable absolute.
5. Wire every threshold to a command. Delete any threshold nothing can check.
6. Output: the filled file plus the list of CI steps still to be added.
