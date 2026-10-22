# CONSTRAINTS.md — Quality Bar (project contract)

> Copy this file to the **project root** as `CONSTRAINTS.md` and fill in the
> numbers. Run `/constraints` to have the agent interview you and propose
> defaults. Empty thresholds are not enforceable; `n/a` with a reason is a
> valid answer, a blank is not.
>
> Some rows below name a tool. If that tool does not exist in your environment
> and cannot be installed, do not leave the row aspirational: either implement
> the check with what you do have, or mark it `n/a` with the reason. And before
> trusting any number here, validate the measurement itself — see
> `constraint-driven-development`, "Validate the instrument".

**Change rule:** lowering any number in this file is a standalone pull request
with its own justification. It never rides along inside a feature change.

## Verification commands

The commands `/verify` runs, in phase order, from the project root. Use the
project's own wrappers (`make`, `./gradlew`, package scripts), not global tools.
A phase that does not apply gets `n/a` and a reason instead of a command.

| Phase | Command |
|---|---|
| build | `______` |
| types | `______` |
| lint | `______` |
| test | `______` |
| security | `______` |

## 1. Correctness

| Dimension | Threshold | Measured by | Status |
|---|---|---|---|
| Line coverage, overall | ≥ `__`% | | |
| Line coverage, core domain modules | ≥ `__`% | | |
| Diff coverage (new/changed lines) | ≥ `__`% | | |
| Mutation score, core domain (optional) | ≥ `__`% | | |
| Skipped/quarantined tests | ≤ `__` , each with a link | | |
| Flaky-test tolerance | 0 unquarantined | | |
| Bug fixes | reproduction test first | PR shows red-then-green | |

## 2. Static analysis

| Check | Threshold |
|---|---|
| Linter | 0 errors |
| Formatter | 0 diffs |
| Type checker | 0 errors; strict in: `______` |
| New suppressions | justification + tracking link required |
| Cyclomatic complexity per function | ≤ `__` |
| File length | ≤ `___` lines (soft) |
| Public API without docstring/comment | 0 |

## 3. Architecture

| Rule | Threshold |
|---|---|
| Dependency-rule violations (inward-only) | 0, enforced by `______` |
| Cross-context imports bypassing the published interface | 0 |
| New third-party dependency | requires the dependency gate |
| Cyclic dependencies between modules | 0 |
| Public interface changes | require versioning + compatibility note |

## 4. Performance

| Path | Budget (p95) | Measured by |
|---|---|---|
| Critical user request | `___` ms | |
| Background job per item | `___` ms | |
| Build time | `___` min | |
| Test suite (fast tier) | `___` min | |
| Frontend LCP / INP / CLS | `___` / `___` / `___` | |
| Unbounded query or allocation | not permitted | review + profiling |
| Agent context loaded at session start | ≤ `____` tokens | contract + profile + skill catalog |
| Agent cost per task (median) | ≤ `____` tokens or currency | the harness's usage report |

## 5. Reliability

| Dimension | Target |
|---|---|
| SLO: availability | `___`% over `___` days |
| SLO: latency | `___`% of requests under `___` ms |
| Error budget policy | when exhausted: `______` |
| Every external call | timeout + retry policy + idempotency where it writes |
| Rollback path | documented and exercised for every release |
| Recovery: RPO / RTO | `___` / `___` |

## 6. Security and privacy

| Rule | Threshold |
|---|---|
| Secrets in repository | 0 (scanner in CI) |
| Real env files tracked (`.env`, `.env.*`) | 0 (`check_env.py`) |
| Variables read by code but missing from `.env.example` | 0 (`check_env.py --strict`) |
| Agents able to read `.env` | 0 — deny rules for every agent in use |
| Known high/critical dependency vulnerabilities | 0 |
| Untrusted input reaching an interpreter unparameterized | 0 |
| Personal data fields | inventoried, justified, retention stated |
| Authentication/authorization changes | threat-modeled before merge |
| License allow-list violations | 0 |

## 7. Operability

| Rule | Threshold |
|---|---|
| New user-facing feature without telemetry | not permitted |
| Alert without a documented response | not permitted |
| Runbook for every on-call alert | required |
| Structured logs with correlation id | required |

## 8. Bar protection

The agent stops and reports — it does not proceed — when a change contains any
trigger listed in `CLAUDE.md` §4. Reaching green by lowering a number here is
never an acceptable resolution.
