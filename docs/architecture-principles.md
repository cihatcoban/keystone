# Architecture Principles

The convictions the skills encode. When two skills seem to conflict, decide by
these.

## 1. Optimize for change, not for elegance

Software is read and modified far more than it is written. The measure of a
design is how cheaply the *next* change lands, not how clever it looks today.
A structure that is beautiful and expensive to change is a bad structure.

## 2. Reversibility is the most valuable property

Classify every decision: reversible, costly, or one-way door. Spend effort in
proportion. Most teams deliberate over reversible choices and slide into
one-way doors without noticing — data formats, public contracts, vendor
coupling, security models.

## 3. Complexity must be paid for by a force that exists today

Every abstraction, service boundary, queue and cache is paid for daily in
comprehension and operations. "We might need it" is not a force. Add complexity
when a real constraint demands it, and remove it when the constraint goes away.

## 4. Boundaries are the architecture

What is allowed to know about what determines everything else: testability,
team autonomy, blast radius, the cost of change. Dependencies point inward,
toward business rules. Business rules know nothing about frameworks, transports
or storage.

## 5. Make illegal states unrepresentable

A guarantee enforced by a type or a database constraint holds forever. A
guarantee maintained by discipline holds until the next tired afternoon. Push
correctness down the stack: types, then constraints, then tests, then review,
then documentation — in that order of reliability.

## 6. The network changes everything

A function call across a process boundary becomes a new failure mode, a
versioning obligation, a latency budget and a debugging problem. Distribute
because you must (independent scaling, deployment cadence, isolation,
ownership), never for tidiness. A modular monolith with enforced internal
boundaries is usually the better trade, and it keeps the option open.

## 7. Correctness under concurrency is designed, not reviewed

Races are not caught by care. Remove shared mutable state, confine ownership,
or let the database arbitrate. Locks are the last resort.

## 8. Failure is the normal case

Timeouts everywhere. Idempotent writes. Bounded retries with jitter. Bounded
queues. Fail fast rather than slow — a hanging request harms everyone, an error
harms one. Design the degraded mode deliberately; it will be used.

## 9. If you cannot observe it, you cannot operate it

Instrumentation ships with the feature, like tests. Correlation ids everywhere.
Alert on symptoms users feel, with a runbook. A business metric catches outages
that infrastructure metrics miss.

## 10. Evidence beats confidence

Measure before optimizing. Reproduce before fixing. Test the failure path, not
just the reasoning about it. A confident explanation with no measurement behind
it is a hypothesis — treat it as one, including when it is your own.

## 11. Deletion is a feature

Every line is maintained, patched and explained forever. Removing code, flags,
dependencies and features is engineering work with its own method
(`deprecation-and-migration`), not cleanup to do when there is time.

## 12. Decisions must outlive the people who made them

The reason is invisible in the code and is exactly what the next engineer
cannot reconstruct. Record it, keep it immutable, supersede rather than edit.

## 13. Conway's law is a constraint, not a proverb

A boundary that cuts across team communication lines erodes. Design the system
and the organization together, or the organization wins.

## 14. The bar must be mechanical

A standard enforced by intention decays within a quarter. Numbers in a file,
checks in CI, and a stop rule for the agent — otherwise you have preferences,
not standards.
