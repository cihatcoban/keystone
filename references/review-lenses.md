# Review Lenses

Lookup for `code-review-and-quality` (see
[ADR-002](../docs/adr/ADR-002-stack-specific-references.md)): the defects that
are specific to one language and that a generic review misses. It adds no
rules; it shows where the skill's axes usually fail in that language.

**Checked against:** TypeScript 5 / ECMAScript 2024, Python 3.12, Go 1.22,
Java 21, Kotlin 2, .NET 8, Rust (2021 and 2024 editions), Swift 6, C++20, SQL
as implemented by PostgreSQL and MySQL, POSIX shell and bash — on 2026-10-22.
For a language not listed, review with the skill alone and say the lens was
missing.

## How to use

1. Read the section for **each language the diff touches** — a change with a
   migration and a handler needs two lenses.
2. Confirm the project's own tools ran on the diff (type checker, linter,
   `CONSTRAINTS.md` verification commands). Do not hand-check what a tool
   already enforces; check that the tool ran and nothing was suppressed.
3. Each item is something tools miss by default, or catch only with a rule the
   project may not enable. Report hits in the skill's finding format, with the
   impact stated for this codebase.

## TypeScript / JavaScript

- **Floating promise** — an async call neither awaited, returned nor given a
  `.catch`; errors vanish and ordering breaks. `forEach` with an async callback
  is the common form: nothing waits for it.
- **Types asserted, not checked, at a boundary** — `as`, `any` or `!` on
  parsed JSON, a response body or user input. The type is a claim; validate
  with a schema where data enters.
- **`||` for defaults** where `0`, `""` or `false` are valid values; use `??`.
- **`sort()` without a comparator** sorts numbers as strings (`[10, 9, 1]` →
  `[1, 10, 9]`) and mutates the array in place.
- **Numbers that are not safe**: money in floating point; 64-bit ids parsed
  into `number` (precision lost above 2^53).
- **Untrusted keys on plain objects** — merging user input into an object, or
  using user strings as keys (`__proto__`); use `Map` or a null-prototype
  object.
- **Dates** parsed from non-ISO strings, or local time used where UTC was meant.

## Python

- **Mutable default argument** (`def f(items=[])`) shared across calls.
- **Blocking call inside `async def`** — a synchronous HTTP client, `time.sleep`,
  a sync database driver — stalls every task on the event loop.
- **Naive datetimes**; `datetime.utcnow()` returns a naive value and is
  deprecated since 3.12 — use `datetime.now(timezone.utc)`.
- **Late-binding closure** in a loop: every `lambda` sees the last value.
- **`is` used for value equality** (works for small ints by accident).
- **Unsafe deserialization** of untrusted input: `pickle`, `yaml.load` without
  a safe loader.
- **Float for money**; use `Decimal` with an explicit context.
- **Type hints with no checker in CI** — they document intent and prove nothing.

## Go

- **Error ignored** (`_ =` or an unchecked return), or wrapped with `%v` instead
  of `%w`, so `errors.Is` / `errors.As` stop working upstream.
- **Goroutine with no way to stop** — no `context` cancellation or close
  signal — leaks under load.
- **Loop variable captured** by a goroutine or closure in a module whose `go`
  directive is below 1.22 (shared across iterations there).
- **`defer` inside a loop** holds every resource until the function returns.
- **Typed nil in an interface** — a nil pointer returned as `error` is not
  `== nil`.
- **Struct containing a mutex copied** by value (`go vet` copylocks).
- **HTTP client without a timeout** — the default client has none.
- Tests touching concurrency run with the race detector.

## Java / Kotlin

- **Resource not closed** — streams, connections, files outside
  try-with-resources (Java) or `use {}` (Kotlin).
- **Broad catch** of `Exception` / `Throwable`; `InterruptedException`
  swallowed without restoring the interrupt flag.
- **`equals` without `hashCode`**; `BigDecimal.equals` compares scale
  (`1.0` ≠ `1.00`) — use `compareTo` for value equality.
- **Proxy-based annotations** (transactions, caching, retries) on a method
  called from inside the same class — the call bypasses the proxy.
- **Shared mutable static state**; non-thread-safe formatters held in fields.
- Kotlin: **`!!`** on values that can be absent; **`GlobalScope`**;
  **`runBlocking`** on a request thread or inside a coroutine; **catching
  `CancellationException`** through a broad `catch (e: Exception)`, which
  breaks structured cancellation; Java platform types assumed non-null.

## C# / .NET

- **`async void`** outside event handlers — exceptions escape every handler.
- **Blocking on tasks** — `.Result`, `.Wait()`, `GetAwaiter().GetResult()` —
  deadlocks under a synchronization context and starves the thread pool.
- **`CancellationToken` accepted but not passed** to the calls below.
- **`IDisposable` without `using`**; a new `HttpClient` per request exhausts
  sockets — use the client factory.
- **`DateTime.Now`** where UTC or `DateTimeOffset` was meant.
- **Deferred `IEnumerable` enumerated twice** — the query runs twice.
- **Null-forgiving `!`** silencing a nullable-reference warning at a boundary.

## Rust

- **`unwrap()` / `expect()`** in non-test code on input that can fail.
- **`unsafe` without a `// SAFETY:` comment** naming the invariant upheld.
- **A `std::sync::Mutex` guard held across `.await`**, or blocking work in an
  async task without moving it to a blocking pool.
- **Integer overflow** — panics in debug, wraps silently in release; use
  `checked_*` / `saturating_*` where it matters. `as` casts truncate silently;
  prefer `TryFrom`.
- **`.clone()` added to satisfy the borrow checker** in a hot path.

## Swift

- **Force operations** — `!`, `try!`, `as!` — on data from outside the process.
- **Reference cycles**: escaping closures capturing `self` strongly; delegates
  not declared `weak`.
- **UI state touched off the main actor**; missing `@MainActor`.
- **Strict-concurrency checks silenced** with `@unchecked Sendable` or
  `nonisolated(unsafe)` without a written justification.
- **Tasks not cancelled** when their owner goes away; long loops that never
  check `Task.isCancelled`.

## C / C++

- **Manual ownership** — raw owning pointers, `new`/`delete` — where RAII or a
  smart pointer belongs.
- **Lifetime errors**: use after move, references to temporaries, iterators
  invalidated by modifying the container.
- **Undefined behavior**: signed overflow, out-of-bounds access, signed and
  unsigned comparison. Review cannot find UB reliably — confirm sanitizers
  (address, undefined, thread) run in CI.
- **Polymorphic base without a virtual destructor.**
- C: unchecked return values (`malloc`, `read`); unbounded `strcpy` /
  `sprintf`.

## SQL and migrations

- **New predicate without a supporting index** — read the query plan, do not
  guess.
- **Function or implicit cast on an indexed column** (`WHERE lower(email) = …`,
  comparing a text column to a number) — the index is skipped.
- **`NOT IN` over a nullable subquery** returns no rows once any NULL appears;
  use `NOT EXISTS`.
- **`SELECT *`** in application code — a column added later changes results.
- **Locking migration** on a large table: index built without the engine's
  online option, a column rewrite, a constraint validated in one step
  (`data-modeling-and-storage`).
- **Multi-statement change outside a transaction**; `UPDATE` / `DELETE` whose
  `WHERE` was not reviewed against real row counts.

## Shell

- **No fail-fast** — scripts that must stop on error lack `set -euo pipefail`
  (or the POSIX subset).
- **Unquoted expansions** (`$var` instead of `"$var"`) — word splitting and
  globbing on file names with spaces.
- **Destructive command on a variable that may be empty** — `rm -rf
  "$dir/"`; use `"${dir:?}"`.
- **Secrets on the command line** (visible in the process list) or echoed by
  `set -x`.
- Confirm `shellcheck` runs on changed scripts.
