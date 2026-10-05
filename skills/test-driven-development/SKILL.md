---
name: test-driven-development
description: Drives implementation with a failing test first and proves bug fixes with a reproduction test. Use when writing any logic or fixing any defect. Triggers - write a test, TDD, red-green-refactor, fix this bug, prove it works, test first, reproduce the bug, is this covered.
---

# Test-Driven Development

A test written after the code tends to assert what the code does. A test written
before asserts what it *should* do — that difference is the whole value. TDD is
not about coverage; it is about having a specification you can execute, and a
design pressure that makes untestable structures uncomfortable early.

## The cycle

**RED** — write the smallest failing test. Run it. *Watch it fail, and read the
failure message.* A test that passes immediately is testing nothing. A failure
message you cannot understand is a test you will curse in six months.

**GREEN** — the simplest code that passes. Not the general solution — the
simplest one. Generality arrives when a second test demands it.

**REFACTOR** — with the suite green, improve names and structure. No behavior
change here.

Each cycle is minutes, not hours. A cycle that takes an hour means the step was
too big.

## Bug fixes: reproduce before repair

Non-negotiable order:

1. Write a test that reproduces the reported behavior, using data as close to
   the real report as possible.
2. Run it. **It must fail** — and fail for the reason in the report. If it
   passes, you have misunderstood the bug and are about to fix the wrong thing.
3. Fix.
4. Green.
5. Add the neighbouring case — the same mistake one boundary over. Bugs have
   siblings.

A fix without a test is a fix that will be undone by a future refactor, with
nothing to catch it.

## What to test

Test **behavior through the public interface**, not internals. A test that
reaches into private state is a test that will break on every refactor while
catching no real defects — the worst possible trade.

Always cover:

| Category | Examples |
|---|---|
| Boundaries | 0, 1, n, n+1, empty, max, off-by-one |
| Types of nothing | null, empty string, empty collection, absent field, zero |
| Error paths | Invalid input, dependency failure, timeout |
| Invariants | The rule that must always hold, asserted directly |
| Regression | Every fixed bug, permanently |

Where behavior is boundary-heavy, table-driven tests (one case per row) beat
many near-identical test functions.

## Test quality

- **One reason to fail per test.** A test asserting six unrelated things tells
  you little when it goes red.
- **Name the behavior, not the function**: `rejects_transfer_when_balance_insufficient`
  beats `test_transfer_2`.
- **Arrange–Act–Assert**, visibly separated.
- **No logic in tests.** A conditional or loop in a test is a second
  implementation you are not testing.
- **Deterministic.** Freeze time, seed randomness, no reliance on ordering, no
  sleeps — wait on a condition instead.
- **No network, no shared database state** in the fast tier. Tests that talk to
  the outside world belong in a slower, clearly separated tier
  (`testing-strategy`).
- **Independent.** Any test runs alone and in any order.

## When TDD is the wrong tool

Be honest about these rather than performing the ritual:

- Exploratory spikes — write throwaway code, learn, then delete it and TDD the
  real implementation
- Pure configuration, glue and generated code
- UI visual arrangement — assert behavior and accessibility; use snapshots
  narrowly and review them like code
- Cases where the correct output is unknown until you see it — characterize
  first (`refactoring-and-simplification`)

## Mocking discipline

Mock at architectural boundaries you own the contract for (a port), not
internal collaborators. Over-mocked tests pass while the system is broken,
because every interaction is an assumption you wrote yourself. For external
services prefer a fake implementation or recorded real responses over
hand-written mocks.

## Exit checklist

- [ ] Every new behavior had a test that was observed failing first
- [ ] Every bug fix has a reproduction test that failed before the fix
- [ ] Boundaries, empties and error paths covered
- [ ] Tests assert through public interfaces only
- [ ] No sleeps, no real clock, no network in the fast tier
- [ ] Each test has one reason to fail and a behavioral name
- [ ] Full suite green, not just the focused test
