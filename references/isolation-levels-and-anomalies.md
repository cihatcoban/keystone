# Isolation Levels and Concurrency Anomalies

What each level prevents, what it does not, and the defense.

## Anomalies

| Anomaly | What happens |
|---|---|
| Dirty read | You read data another transaction has not committed |
| Non-repeatable read | The same row reads differently twice in one transaction |
| Phantom read | A range query returns new rows on a second read |
| **Lost update** | Two read-modify-write sequences interleave; one change vanishes |
| **Write skew** | Both transactions read an overlapping set, each sees its invariant hold, both write, invariant now violated |
| Read skew | Two related rows read at different points, mutually inconsistent |

## Levels

| Level | Prevents | Still possible |
|---|---|---|
| Read uncommitted | — | Everything |
| **Read committed** (most common default) | Dirty reads | Non-repeatable, phantoms, **lost update**, write skew |
| Repeatable read / snapshot | + non-repeatable reads (and phantoms in MVCC engines) | **Write skew**, lost update in some engines |
| Serializable | All | Nothing — expect serialization failures and retry |

**The two facts that cause production bugs:**

1. Your default is probably read committed, which does **not** protect
   `SELECT` → compute → `UPDATE`.
2. Snapshot isolation does **not** prevent write skew. The classic case: two
   on-call doctors each check "is at least one other doctor on call?", both see
   yes, both go off call.

## Defenses

| Problem | Defense | Cost |
|---|---|---|
| Lost update | Atomic statement: `SET x = x - 1 WHERE x >= 1` | None — always prefer |
| Lost update | Optimistic: `WHERE version = ?`, check affected rows, retry | Retry logic |
| Lost update | Pessimistic: `SELECT ... FOR UPDATE` | Contention, deadlock risk |
| Write skew | Serializable isolation | Serialization failures to retry |
| Write skew | Materialize the conflict (lock a row representing the constraint) | Extra row and lock |
| Uniqueness | Unique constraint | None — let the database decide |
| Phantom in a range | Predicate lock or serializable | Contention |

## Rules

- Check affected row counts on conditional updates. Zero rows means conflict,
  not success.
- Retry serialization failures at a well-defined layer, with a bounded count.
- Keep transactions short; never perform network I/O inside one.
- Order locks consistently (for example, ascending primary key) to make
  deadlock cycles impossible.
- Set a lock timeout; waiting forever is not resilience.
- Distributed locks are advisory — a lease can expire while the holder still
  believes it holds it. Use a fencing token or make the operation idempotent.
