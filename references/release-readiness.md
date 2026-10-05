# Release Readiness Checklist

## Gates
- [ ] All CI checks green — not "green except the known flaky one"
- [ ] Build is versioned, reproducible, and the artifact is the one tested
- [ ] Dependency and secret scans clean
- [ ] Changelog written for consumers; version matches the change class

## Compatibility
- [ ] New code works with the currently deployed schema
- [ ] Old code survives the new schema (rollback path)
- [ ] API changes are additive, or a version is introduced with a sunset date
- [ ] Event schema changes are backward compatible for existing consumers
- [ ] Config changes have defaults that are safe on an un-updated instance

## Data
- [ ] Migration is one phase of expand/contract, and reversible
- [ ] Long backfill runs outside the deploy, batched and resumable
- [ ] Backup verified immediately before any destructive step

## Rollout
- [ ] Strategy chosen: rolling, blue/green, canary, or flag percentage
- [ ] Observation window and the exact metrics to watch, written down
- [ ] Numeric rollback trigger (error rate, latency, business metric)
- [ ] Named owner watching, for the defined duration
- [ ] Rollback path exercised, not assumed

## Observability
- [ ] Telemetry for the new behavior is deployed and confirmed emitting
- [ ] Dashboard updated; alert thresholds reviewed for the new load shape
- [ ] Runbook exists for any alert this change can trigger

## Communication
- [ ] Affected teams and support know what is changing and when
- [ ] Status page / release notes prepared if user-visible
- [ ] On-call briefed on what to watch and how to roll back

## After
- [ ] Signals watched for the full window before declaring success
- [ ] Flag removal scheduled
- [ ] Anything surprising recorded; two surprises in one area is a process fix
