# Failure Modes Catalog

Prompts for design review and incident triage. Ask "what happens when…" against
each row for the component in front of you.

## Network and dependencies
| Failure | Common mishandling |
|---|---|
| Dependency slow, not down | No timeout → connection pool exhausted → total outage |
| Dependency returns 200 with an error body | Treated as success; corruption downstream |
| Dependency returns unexpected shape | Parser throws, or silently coerces to a wrong default |
| Connection dropped mid-response | Partial read parsed as complete |
| DNS failure / certificate expiry | No alert until users report it |
| Retry storm during recovery | Unjittered retries prevent the dependency from recovering |
| Cascading failure | No breaker or bulkhead; one dependency takes down all handlers |

## State and data
| Failure | Common mishandling |
|---|---|
| Duplicate message / double submit | Non-idempotent write creates two records |
| Out-of-order delivery | Later state overwritten by an earlier message |
| Concurrent update | Read-modify-write loses one change |
| Partial write across two stores | No outbox; DB committed, event lost |
| Clock skew | Ordering by timestamp produces wrong sequence |
| Unicode / very long / empty input | Truncation, mojibake, or a crash in an unrelated layer |
| Timezone boundary, DST | Off-by-one-day bugs in scheduled work |
| Data growth | Query that was fast at 10k rows is fatal at 10M |

## Resources
| Failure | Common mishandling |
|---|---|
| Memory growth | No bound on a cache or queue; OOM kill |
| Connection/file-handle leak | Works until sustained load, then fails everywhere |
| Unbounded queue | Converts throughput problem into a crash |
| Disk full | Logs fill the volume and take the service down |
| Thread/event-loop starvation | One blocking call stalls everything |

## Deployment and operations
| Failure | Common mishandling |
|---|---|
| Old and new code running together | Migration assumes one version |
| Rollback with a migrated database | Old code cannot read the new schema |
| Config change without deploy | Untested path enabled in production |
| Flag default wrong on a new instance | Feature on before it is ready |
| Cold start / empty cache | Thundering herd on restart |
| Scheduled job overlap | Two runs of the same job corrupt state |

## Human and process
| Failure | Common mishandling |
|---|---|
| Alert fires with no runbook | Responder improvises at 3am |
| Only one person understands it | Unavailable exactly when needed |
| Postmortem action items not tracked | Same incident recurs |
| Silent degradation | Nothing measures the business outcome, only CPU |
