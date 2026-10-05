---
description: Design the structure — decision, boundaries, contracts — before implementation
---

Apply `architecture-decisions`, plus `domain-modeling`,
`boundaries-and-dependencies` and `api-and-contract-design` as relevant.

Input: $ARGUMENTS

1. Classify the decision: reversible, costly, or one-way door. Say which.
2. Write the forces before the options. Generate at least three options,
   including extending what exists.
3. Compare options against the forces in a table; name what each rejected
   option was better at.
4. For a one-way door: spike the riskiest assumption before committing.
5. Define the boundaries and the contracts that result — module placement,
   dependency direction, interface shape, compatibility stance.
6. Record an ADR in `docs/adr/`; link it from the spec.
