# Glossary

Terms used across the skills with a specific meaning.

**Aggregate** — the consistency boundary that owns an invariant; the unit
loaded and saved together. One transaction modifies one aggregate.

**Anti-corruption layer** — translation at your boundary so another system's
model does not leak into yours.

**Backpressure** — bounded queues that reject or shed load when full, rather
than accumulating until memory runs out.

**Bar protection** — stopping when a change reaches green by weakening a check
rather than fixing the problem (`CLAUDE.md` §4).

**Bounded context** — a boundary inside which a term has exactly one meaning.

**Bulkhead** — isolated resource pools so one slow dependency cannot consume
all capacity.

**Characterization test** — a test that captures current behavior (correct or
not) so that refactoring is safe.

**Contract test** — a test that fails when two sides of an interface drift
apart, run at build time rather than discovered in production.

**Diff coverage** — coverage of changed lines only; the ratchet that improves a
legacy codebase without a rewrite.

**Error budget** — the failure allowed by an SLO, used as a decision rule:
budget healthy, ship; budget spent, fix reliability.

**Expand / contract** — add the new alongside the old, migrate, then remove the
old. Three deploys, each reversible.

**Fencing token** — a monotonically increasing value proving a lock holder is
still current; the only safe way to use a distributed lock.

**Golden signals** — latency, traffic, errors, saturation.

**Idempotency** — running the operation twice has the same effect as once.
Required of every write that can be retried, which is all of them.

**Invariant** — a rule that must never be false. Each has exactly one enforcing
owner.

**Little's law** — concurrency = arrival rate × time in system; explains why
latency explodes near saturation.

**One-way door** — a decision that is practically irreversible. Prototype the
risky assumption first.

**Outbox** — writing the business change and the outgoing message in one local
transaction so an event is never lost or emitted for a rolled-back change.

**Port / adapter** — the interface the core defines, and the outer
implementation of it. Dependencies point inward.

**Saga** — a multi-step workflow of local transactions with explicit
compensating actions. Design the compensation first.

**Shadow comparison** — running the new path alongside the old, serving the
old, logging the differences. The evidence that a replacement is correct.

**SLI / SLO** — the measurement of user-visible behavior, and the target for it
over a window.

**Strangler fig** — replacing a system capability by capability behind a seam,
so you can stop at any point.

**Vertical slice** — a unit of work crossing every layer to produce observable
behavior, as opposed to building a layer at a time.

**Walking skeleton** — one thin end-to-end path through every layer, built
first, proving integration and deployment exist.

**Write skew** — two transactions each preserving an invariant in their own
view, jointly violating it. Survives snapshot isolation.
