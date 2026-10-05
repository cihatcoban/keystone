# Performance Budgets

Starting values. Adjust per product, then enforce — an unenforced budget is a
preference.

## Backend
| Path | p50 | p95 | p99 |
|---|---|---|---|
| Read endpoint (cached) | 20 ms | 80 ms | 200 ms |
| Read endpoint (database) | 50 ms | 200 ms | 500 ms |
| Write endpoint | 80 ms | 300 ms | 800 ms |
| Background job, per item | — | 250 ms | 1 s |

Rules of thumb: no more than ~5 database round trips per request; zero queries
inside loops; every list bounded; every external call has a timeout shorter
than the caller's remaining budget.

## Frontend
| Metric | Target | Notes |
|---|---|---|
| LCP | ≤ 2.5 s | Mid-range device, throttled network |
| INP | ≤ 200 ms | Interaction to next paint |
| CLS | ≤ 0.1 | Reserve space for async content |
| Initial JS, compressed | ≤ 200 KB | Enforce in CI |
| Initial CSS | ≤ 50 KB | |
| Fonts | ≤ 2 families, subset, `font-display: swap` | |

## Build and test
| Stage | Budget |
|---|---|
| Fast test tier | ≤ 2 min |
| Full CI pipeline | ≤ 10 min |
| Local incremental build | ≤ 10 s |
| Container image | ≤ 500 MB |

## Capacity
- Steady-state utilization ≤ 60–70%. Above ~80%, latency enters the steep part
  of the queueing curve (Little's law) and small load increases produce large
  latency increases.
- Headroom for the largest single failure domain (one instance, one zone).
- Know the resource that runs out first, from a load test — not from a guess.

## Enforcement
- Bundle-size check in CI, failing on regression
- Query-count assertion on critical endpoints (catches N+1 permanently)
- Benchmark with a regression threshold for core algorithms
- Alert on the SLI, not on the budget — the budget is for development, the SLO
  is for production
