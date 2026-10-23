# Migration Engine Lookup

Lookup for `data-modeling-and-storage` (see
[ADR-002](../docs/adr/ADR-002-stack-specific-references.md)): what each common
schema change costs in a given engine — whether it rewrites the table, which
lock it holds, and the online form. The skill's rules (expand / contract,
batched backfills, one phase per deploy) still apply; this file says how to
meet them in each engine.

**Checked against:** PostgreSQL 18, MySQL 8.4 (InnoDB), SQLite 3 — official
documentation, on 2026-10-23. Older versions behave differently; confirm the
project's engine version during stack discovery. For an engine not listed,
apply the skill and find the engine's own online-DDL documentation before the
migration runs, not after it locks a table.

## Before any engine

- **Bound the lock wait.** A DDL statement that waits for its lock queues every
  later query on that table behind it. One long-running transaction plus an
  unbounded wait is an outage. Set a short lock timeout for the migration
  session and retry on timeout.
- **Measure on production-sized data.** The cost of a rewrite grows with the
  table; a migration that takes 40 ms on a fixture can hold a lock for an hour.
- **State the online form explicitly** where the engine allows it, so the
  statement fails instead of silently falling back to a blocking one.

## PostgreSQL 18

Lock timeout: `SET lock_timeout = '5s';` in the migration session. It limits
each lock wait separately; `statement_timeout` limits total run time.

| Change | Online form | Cost if done naively |
|---|---|---|
| Add a column, no default or a non-volatile default | `ADD COLUMN` directly — the default is stored in metadata | — |
| Add a column with a volatile default (`clock_timestamp()`), a stored generated column, or an identity column | Add it nullable without the default; backfill in batches; then set the default | Rewrites the table and its indexes |
| Make an existing column `NOT NULL` | `ADD CONSTRAINT c CHECK (col IS NOT NULL) NOT VALID` → `VALIDATE CONSTRAINT c` → `ALTER COLUMN col SET NOT NULL` (skips the scan because the valid check proves it) → drop the check | `SET NOT NULL` alone scans the whole table under an exclusive lock |
| Add a foreign key | `ADD CONSTRAINT … FOREIGN KEY … NOT VALID`, then `VALIDATE CONSTRAINT` (takes only `SHARE UPDATE EXCLUSIVE`, plus `ROW SHARE` on the referenced table) | A full validating scan while blocking writes |
| Add an index | `CREATE INDEX CONCURRENTLY` — outside a transaction block; one concurrent build per table at a time | Plain `CREATE INDEX` blocks writes for the whole build |
| Failed concurrent index build | It leaves an `INVALID` index that still costs writes (and, if unique, still enforces uniqueness): drop it and rebuild, or `REINDEX INDEX CONCURRENTLY` | Silent write overhead |
| Change a column type | Expand / contract: new column, dual write, batched backfill, switch reads, drop the old one | Rewrites the table and rebuilds indexes, except binary-coercible changes such as `varchar` → `text` |
| Rename a column | Expand / contract (or a view) while old application versions run | Instant, but the running old version breaks |
| Drop a column | Stop reading and writing it first; then `DROP COLUMN` (marks it dropped, no rewrite) | The previous application version errors |

Migration tools that wrap each file in a transaction need their documented
escape hatch for `CONCURRENTLY`; check the tool before writing the migration.

## MySQL 8.4 (InnoDB)

Lock timeout: `SET SESSION lock_wait_timeout = 5;` bounds the wait for the
metadata lock. Every online DDL still takes a brief exclusive metadata lock to
commit; it waits for open transactions on the table, and while it waits it
blocks new queries on that table. Find long-running transactions first.

Write `ALGORITHM=INSTANT` or `ALGORITHM=INPLACE, LOCK=NONE` in the statement:
if the engine cannot honor it, the statement fails instead of copying the
table.

| Change | Algorithm | Concurrent writes |
|---|---|---|
| Add a column | `INSTANT` (default) | Yes; an auto-increment column needs at least `INPLACE, LOCK=SHARED` |
| Drop a column | `INSTANT` | Yes |
| Add a secondary index | `INPLACE` | Yes |
| Make a column `NOT NULL` | `INPLACE`; needs strict SQL mode, fails if NULLs exist — backfill first | Yes |
| Rename a column | `INSTANT` when type and nullability are unchanged; `INPLACE` if another table's foreign key references it | Yes |
| Add a foreign key | `INPLACE` only with `foreign_key_checks` disabled; otherwise `COPY` | Not with `COPY` |
| Change a column type | `COPY` only | **No** — use expand / contract, or an online schema-change tool that copies into a shadow table |

`INSTANT` add and drop are limited to 64 row versions per table in 8.4
(`INFORMATION_SCHEMA.INNODB_TABLES.TOTAL_ROW_VERSIONS`); a table rebuild resets
the count. At the limit the statement errors and needs `INPLACE` or `COPY`.

## SQLite 3

Direct `ALTER TABLE` covers rename table, rename column, add column and drop
column. `ADD COLUMN` cannot add a `PRIMARY KEY` or `UNIQUE` column, a
`NOT NULL` column needs a non-null default, and the default cannot be
`CURRENT_TIMESTAMP` or an expression in parentheses.

Anything else — changing a type, adding `UNIQUE`, `CHECK`, `NOT NULL` or a
foreign key to an existing column, reordering — uses the documented rebuild,
in one transaction:

1. `PRAGMA foreign_keys=OFF` (if enabled), then begin.
2. Save the table's indexes, triggers and views from `sqlite_schema`.
3. Create the new table under a **temporary name**, copy rows into it, drop the
   old table, rename the new one to the old name — never rename the old table
   first; that corrupts references in triggers, views and foreign keys.
4. Recreate the indexes, triggers and views.
5. `PRAGMA foreign_key_check`, commit, `PRAGMA foreign_keys=ON`.

SQLite allows one writer at a time, so the rebuild blocks every writer until it
commits. Size the transaction to what the application can wait for.

## Backfills, any engine

- Batch by primary-key range or a keyset cursor, a few thousand rows per
  transaction, committed per batch, with a pause between batches.
- Make each batch idempotent (`WHERE new_col IS NULL`), so a restart resumes.
- Record progress; watch replication lag and lock waits while it runs; stop at
  a threshold rather than pushing through.
