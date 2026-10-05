# Definition of Done

A task is done when **all** applicable statements are true and observed — not
reasoned about. Partial truth means not done.

## Always
- [ ] Acceptance criterion from the spec is satisfied
- [ ] A test was written, observed failing, and now passes
- [ ] Full suite green (not only the focused test)
- [ ] Lint, format and type checks clean
- [ ] No new suppression without a justification and a tracking link
- [ ] One logical change per commit; message explains *why*
- [ ] Incomplete behavior is behind a flag defaulting to off
- [ ] Anything deferred is recorded as an issue, not remembered

## Touching data or schema
- [ ] Migration is expand/contract; each phase works with the previous app version
- [ ] `down` migration exists and is exercised in CI
- [ ] Backfill is batched and resumable
- [ ] Destructive change is in its own change set, after a verified backup

## Touching an interface others call
- [ ] Compatibility class assessed (compatible vs breaking)
- [ ] Schema checked in; CI diffs it for breaking changes
- [ ] Error contract defined: stable codes, retryability, correlation id
- [ ] Deprecation path published if anything is being replaced

## Touching an external call
- [ ] Connect and read timeouts set; total budget below the caller's
- [ ] Retries bounded and jittered, only on retryable classes, at one layer
- [ ] Write path is idempotent, with the result stored against the key
- [ ] Failure path tested, not just reasoned about

## Touching security-relevant code
- [ ] Input validated at the boundary; queries parameterized
- [ ] Object-level authorization enforced at the data layer
- [ ] Negative authorization test exists
- [ ] No secret or personal data in code, logs or errors

## Shipping
- [ ] Telemetry for the new behavior exists and was verified after deploy
- [ ] Rollback path tested, with a numeric trigger
- [ ] Runbook updated if an alert can now fire
- [ ] Flag removal scheduled as a task
