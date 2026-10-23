# CONSTRAINTS.md — Keystone Quality Bar

Keystone's own quality contract. Projects that install Keystone start from
`templates/CONSTRAINTS.template.md` instead; this file holds the numbers for
this repository only.

Every row names the check that enforces it. "Current" was measured on
2026-10-23 against `release/3.0.0`. `n/a` rows state why the dimension
does not apply to a repository of process documentation and stdlib-only
tooling.

**Change rule:** lowering any number in this file is a standalone pull request
with its own justification. It never rides along inside a feature change.

## Verification commands

What `/verify` runs, in phase order. `make all` is what CI runs; the rows split
it so a failure names its phase.

| Phase | Command |
|---|---|
| build | `make adapters-check` |
| types | n/a — no type checker configured; see §2 |
| lint | `make validate` `make triggers` `ruff check .` `ruff format --check .` `make lint` |
| test | `make test` |
| security | `make env-check` |

## 1. Correctness

| Dimension | Threshold | Measured by | Current |
|---|---|---|---|
| Repository validation | 0 errors, 0 warnings | `make validate` (CI) | 0 / 0 |
| Skill routing | 0 weak prompts, 0 collisions | `make triggers` (CI) | 0 / 0 across 131 prompts |
| Eval coverage | 1 case file per skill; ≥ 3 positive and ≥ 2 negative prompts | `make validate` (CI) | 34 / 34 |
| Tooling unit tests | 100% passing | `make test` (CI) | 150 / 150 |
| Skipped or quarantined tests | 0 | review | 0 |
| Line coverage, `scripts/` | n/a — no coverage tool; tooling is stdlib-only by rule. Revisit if `scripts/` exceeds 1,500 lines | — | **revisit due:** `scripts/` 2,616 lines, `hooks/` 2,142; 85.7% lines covered, measured once with stdlib `trace` (no gate yet) |
| Bug fixes | reproduction test first | PR shows red-then-green | — |

## 2. Static analysis

| Check | Threshold | Measured by | Current |
|---|---|---|---|
| Markdown lint | 0 errors | `make lint`, pinned `markdownlint-cli2@0.22.1` (CI) | 0 |
| Python lint and format | 0 findings, 0 diffs | `ruff check` + `ruff format --check`, pinned `ruff==0.6.9` (CI + pre-commit) | 0 / 0 |
| Type checker | n/a — none configured; scripts use type hints only | — | — |
| New suppressions | justification + tracking link required | review | 21 `noqa: E402` (sys.path imports in scripts, hooks and tests), justified inline |
| Skill description length | 80–500 chars (hard); ≤ 320 (target) | `make validate`: error outside 80–500, warning above 320 | 217–314 |
| Skill catalog size | ≤ 3,800 tokens (hard); warn above 3,200 | `make validate` (CI) | ≈ 3,055 |
| Skill body length | ≥ 350 words (hard); warn above 1,600 | `make validate` (CI) | 674–1,393 |
| Script file length | ≤ 400 lines (soft) | review | max 413 (`validate_repo.py`) |

## 3. Architecture

| Rule | Threshold | Measured by |
|---|---|---|
| `CLAUDE.md` / `AGENTS.md` contract bodies | byte-identical | `make validate` (CI) |
| Plugin version | identical across every manifest | `make validate` (CI) |
| Generated Gemini commands | 0 stale, 0 orphaned | `make adapters-check` (CI) |
| Third-party Python dependencies in `scripts/` | 0 — standard library only | review |
| Stack assumptions in skill bodies | 0 — stack-agnostic by rule | review (`CONTRIBUTING.md`) |
| A skill overlapping an existing one | not permitted; extend instead | review + `make triggers` |

## 4. Performance

| Path | Budget | Measured by | Current |
|---|---|---|---|
| `make all` locally | ≤ 10 s | `time make all` | 4.1 s |
| Tooling unit tests | ≤ 5 s | `make test` | 3.6 s |
| CI `validate` workflow | ≤ 3 min | GitHub Actions run time | 20–35 s |
| Request latency, frontend vitals | n/a — Keystone ships no service or UI | — | — |

## 5. Reliability

| Dimension | Target |
|---|---|
| SLOs, error budget, RPO / RTO | n/a — no running service |
| Release | version bump in every manifest + `CHANGELOG.md` entry |
| Rollback | install the previous tagged version |

## 6. Security and privacy

| Rule | Threshold | Measured by | Current |
|---|---|---|---|
| Secrets in repository | 0 | `gitleaks` (CI + pre-commit) | 0 |
| Real env files tracked (`.env`, `.env.*`) | 0 | `make env-check` (CI) | 0 |
| `.env` hygiene findings | 0 errors, 0 warnings | `check_env.py --strict` (CI) | 0 / 0 |
| Network calls or writes outside the repo by `scripts/` | 0, except the installers, `verify.py` and `evals_live.py` as listed in `SECURITY.md` | review (`SECURITY.md`) | 0 beyond the listed exceptions |
| Outdated GitHub Actions majors | 0 open > 30 days | Dependabot, monthly | 0 |
| Third-party text or code copied in | listed in `NOTICE`, Apache-2.0 compatible | review | none |
| Personal data | n/a — none collected or stored | — | — |

## 7. Operability

| Rule | Threshold |
|---|---|
| `main` branch | ruleset `protect-main`: no deletion, no force push, `repository` check required and up to date |
| Merged branches | deleted automatically |
| Telemetry, alerts, runbooks | n/a — no running service |

## 8. Bar protection

The agent stops and reports — it does not proceed — when a change contains any
trigger listed in `CLAUDE.md` §4. Reaching green by lowering a number here is
never an acceptable resolution.
