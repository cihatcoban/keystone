# Error handling

Stack-agnostic patterns for code that fails well. Read with
`code-review-and-quality` (failure behavior) and
`distributed-systems-and-resilience` (anything across a network).

## Three kinds of error

| Kind | Example | Handling |
|---|---|---|
| **Expected outcome** | Card declined, item out of stock, validation failed | Part of the domain: a typed result or a specific error type, handled by the caller, shown to the user in their terms |
| **Operational failure** | Timeout, connection refused, disk full, rate limited | Retry if transient and the operation is idempotent; otherwise fail the request cleanly and alert on rate |
| **Programmer error** | Null where a value is guaranteed, broken invariant, impossible state | Do not handle. Fail loudly, close to the cause, and fix the code |

Most error-handling bugs come from treating one kind as another: catching a
programmer error and carrying on with corrupt state, or crashing on an expected
outcome a user can fix.

## Where to handle

- **Handle at the level that can do something about it.** A repository cannot
  decide what the user sees; the request handler can.
- **Translate at boundaries.** A database exception becomes a domain error in
  the adapter; a domain error becomes a status code and body at the API edge.
  Inner layers never see transport details and the API never leaks storage
  details.
- **Log once, at the boundary that handles it,** with context (operation, ids,
  correlation id). Logging at every layer that rethrows produces five copies
  and no clarity.

## Rules that prevent silent failure

1. **Never swallow.** An empty catch, `except: pass`, or an ignored error
   return turns a failure into silence — it is a bar-protection trigger
   (`CLAUDE.md` §4). If ignoring is truly right, say why in a comment.
2. **Catch the narrowest type you can name.** A catch-all around new code hides
   the next bug too.
3. **Wrap with context, keep the cause.** "Loading invoice 42 for tenant 7:
   connection refused", with the original error attached.
4. **Clean up on every path.** Release locks, files and connections with the
   language's guaranteed construct (`finally`, `defer`, `using`, RAII,
   `with`), not by remembering.
5. **Fail fast at startup.** Missing configuration, unreachable required
   dependencies and invalid settings stop the process before it accepts work
   (`configuration-and-secrets`).
6. **Never let an error leave the system half-updated.** One transaction, an
   outbox, or a compensating step — decided before the code is written.

## Errors in contracts

- HTTP APIs: one error shape for every endpoint; RFC 9457 problem details is a
  good default. A stable machine-readable code, a human message, no stack
  traces or internal ids (`references/http-api-conventions.md`).
- Messages and events: a failed message goes to a dead-letter destination with
  the reason, never silently dropped and never retried forever.
- User-facing text says what happened and what the user can do; the log says
  what the engineer needs.

## Retries

Retry only when all hold: the failure is transient, the operation is
idempotent (or made so with a key), and there is a budget — capped attempts
with exponential backoff and jitter, inside the caller's own deadline. A retry
without those is how one slow dependency becomes an outage.

## Testing error paths

- Every handled error has a test that forces it (a fake that throws, a closed
  connection, a full disk) and checks the observable result.
- Test the half-way failure: step one succeeds, step two fails — is the state
  consistent afterwards?
- Assert the error message carries context and the response carries no
  internals.
