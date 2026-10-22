<!-- markdownlint-disable-file MD029 -- adoption steps are numbered 1-20 across
     sections on purpose: the number is the step's position in the whole path. -->

# Adoption Path

Adopting 34 skills at once produces ceremony, not quality. Adopt in the order
that removes the most risk per unit of effort.

## Level 0 → 1: Make the bar visible

Nothing is written down; quality depends on who reviewed it.

1. `/onboard` — the agent stops inventing conventions
2. `/constraints` — measure current values, set targets, install ratchets
3. Turn on the bar-protection triggers in review

**Done when:** an agent can state the project's coverage target, test command
and dependency rule without asking, and a lowered threshold is caught in review.

## Level 1 → 2: Make work verifiable

Changes land, but "done" is decided by whoever is most tired.

1. `spec-driven-development` on anything larger than a day
2. `planning-and-task-breakdown` — vertical slices, no L-sized tasks
3. `test-driven-development` for bug fixes first (the easiest habit to adopt —
   the reproduction test is obviously useful)
4. `code-review-and-quality` with the six axes and a verdict

**Done when:** every merged change has a criterion it satisfies and a test that
was observed failing first.

## Level 2 → 3: Make design deliberate

The code works; the structure is accidental.

1. `architecture-decisions` — start recording, even retroactively for the three
   decisions people keep re-arguing
2. `boundaries-and-dependencies` — draw one line, enforce it with a tool
3. `domain-modeling` if the domain has real rules
4. `api-and-contract-design` for anything with consumers

**Done when:** new code has an obvious home, cycles are impossible, and "why is
it like this?" has a document.

## Level 3 → 4: Make failure survivable

It works until something else does not.

1. `distributed-systems-and-resilience` — timeouts and idempotency first; they
    prevent the most expensive incidents
2. `concurrency-and-consistency` where shared state exists
3. `observability-and-slos` — correlation ids, then golden signals, then SLOs
4. `release-engineering` — tested rollback, staged rollout

**Done when:** you can answer "what happens when X is down?" for every
dependency, and you have rolled back at least once without drama.

## Level 4 → 5: Make improvement systematic

1. `incident-response` with blameless postmortems and tracked actions
2. `deprecation-and-migration` — start removing things on purpose
3. `performance-engineering` with budgets in CI
4. `testing-strategy` — mutation testing on the core, flakiness at zero
5. Your own domain pack

**Done when:** the same incident does not happen twice, and the codebase gets
smaller some months.

## Where teams stall

| Stall | Symptom | Unblock |
|---|---|---|
| Constraints never filled in | `CONSTRAINTS.md` has blanks | Blanks are unenforceable — set a low number now, ratchet later |
| Specs become bureaucracy | Long specs nobody reads | Two pages maximum; criteria are the only mandatory part |
| ADRs for everything | Nobody reads them | Only decisions costly to reverse |
| Review theater | Approvals in under a minute | Start with the bar-protection scan; it is two minutes and finds real things |
| Skills as decoration | Installed, never fires | Routing problem — fix descriptions, run `make triggers` |
