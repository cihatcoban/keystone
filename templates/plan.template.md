# Plan: <spec title>

Spec: `docs/specs/NNN-....md`

## Tasks

- [ ] **T1** — <imperative verb + object>
  - Criterion: <spec §4 criterion number — reference it, do not restate it;
    two wordings of one requirement drift apart>
  - Test: <what proves it>
  - Evidence: RED <command → failing assertion> · GREEN <command → result>
    (filled in while building; see `test-driven-development`)
  - Files: <paths this task owns; no other parallel task touches them>
  - Brief: <2–4 lines a fresh session needs: the pattern to follow
    (`path:line`), the contract to honor, the constraint that applies>
  - Size: S | M | L
  - Depends on: — · Parallel with: <task ids, or —>

- [ ] **T2** — …

## Sequencing rationale

Why this order. Which task resolves the most uncertainty, and why it is first.

## Risk

The task most likely to invalidate this plan, and what we do if it does.

## Rollout

Flag name · first audience · condition to widen · condition to make default ·
who removes the flag and when.

## Changes

Dated, append-only. Split, inserted, skipped, reordered or abandoned tasks,
each with its reason. A plan rewritten without a trace cannot be trusted.

- YYYY-MM-DD — <T3 split into T3a/T3b: migration and backfill must deploy
  separately>

## Cleanup

- [ ] Flag removed
- [ ] Dual-write / old path deleted
- [ ] Docs, dashboards and alerts updated
