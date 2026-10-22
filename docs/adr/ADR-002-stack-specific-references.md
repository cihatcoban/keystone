# ADR-002: Stack-specific lookups live in references, never in skill bodies

- **Status:** proposed
- **Date:** 2026-10-22
- **Deciders:** Cihat
- **Reversibility:** reversible — the references can be deleted without
  changing any skill's rules

## Context

Keystone's skill bodies are stack-agnostic by rule (`CONTRIBUTING.md`,
`CONSTRAINTS.md` §3). A comparison against everything-claude-code 2.2.3 showed
where that rule costs the most: code review and frontend work. An agent that
reviews a Go diff or builds a Vue page needs the handful of mistakes that are
specific to that language or framework, and the agnostic body cannot name them.
ECC answers with one skill or agent per stack — more than 20 reviewers and
framework skills.

Forces:

- **Routing budget.** Every skill description enters every session; the
  catalog is capped at 3,800 tokens and sits near 3,000. One skill per stack
  would exhaust it.
- **Overlap.** A `go-review` skill and `code-review-and-quality` would compete
  for "review this PR"; `CONSTRAINTS.md` §3 forbids overlapping skills.
- **Drift.** Framework idioms change every year; principles do not. Material
  that goes stale must be easy to find, date and replace.
- **Load cost.** A skill body is read every time the skill fires. A Rust lens is
  waste in a Python review.

## Decision

We will keep skill bodies stack-agnostic and put stack-specific material in
shared `references/*.md` files that a body points to and the agent loads only
after stack discovery (`CLAUDE.md` §3) has named the stack.

Each such reference:

1. Is a **lookup**, not a procedure: it maps a principle the body already
   states to that stack's idiom or its most common failure. It never adds a
   rule the body does not have.
2. Opens with a **"Checked against"** line naming the versions and the date.
3. Starts each entry with what the project's tools already catch, so the
   reviewer spends attention on what they miss.
4. Tells the agent what to do for a stack it does not list: apply the body and
   say the lens was missing.

## Options considered

| Option | Fit with forces | Better at | Worse at |
|---|---|---|---|
| A (chosen): agnostic bodies, stack lookups in references | catalog unchanged, no routing overlap | per-stack precision at zero routing cost | one more file to load; lookups need dating |
| B: one skill per language or framework | exhausts the catalog, overlaps core skills | discoverability by name | routing, budget, drift |
| C: stack examples inside skill bodies | bodies grow past 1,400 words | no extra file | every load pays for every stack |
| D: do nothing | keeps the rule pure | simplicity | reviews and UI work miss stack-specific defects |

## Consequences

**Gains:** review and frontend work catch stack-specific defects without new
skills; the catalog and routing are untouched; stale material is isolated in
dated files.

**Costs (paid continuously):** each lookup must be re-checked when a listed
stack ships a major version; an inaccurate lookup is worse than none, because
the agent trusts it.

**New constraints this places on future work:**

- A lookup that needs a rule the body lacks means the body is incomplete — fix
  the body first, stack-agnostically.
- `CONTRIBUTING.md` "Stack-agnostic" applies to skill bodies; references that
  follow this ADR are the one sanctioned place for stack names.

## The assumption most likely to be wrong

That the listed stacks cover most real use. The signal: reviews reporting
"lens missing" for the same stack repeatedly. Add that stack's entry then —
not before.

## Follow-up

- [x] `references/review-lenses.md`, `references/frontend-framework-map.md`,
  `references/api-protocol-checklists.md` follow this shape
- [x] `CONTRIBUTING.md` states the exception and links here
- [ ] Re-check each "Checked against" line at the next major release of a
  listed stack
