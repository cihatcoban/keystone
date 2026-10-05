<div align="center">

# Keystone

**Master-level engineering skills for AI coding agents.**

Architecture-first, stack-agnostic, from intent through operations — with a
written quality contract the agent cannot quietly lower.

[![License: Apache 2.0][license-badge]](LICENSE)
[![Validate][ci-badge]][ci]
![Version][version-badge]
![Skills][skills-badge]

[Quick start](#quick-start) · [Commands](#commands) · [Skills](#skills) ·
[How it works](#how-it-works) · [Contributing](CONTRIBUTING.md)

</div>

```text
  DEFINE            ARCHITECT              BUILD            VERIFY           OPERATE
 ┌────────┐      ┌─────────────┐       ┌──────────┐     ┌──────────┐     ┌──────────┐
 │ intent │ ───▶ │  decision   │ ───▶  │  slice   │ ──▶ │  review  │ ──▶ │  ship    │
 │  spec  │      │ boundaries  │       │  test    │     │  debug   │     │ observe  │
 │  plan  │      │  contracts  │       │ refactor │     │ perf/sec │     │ respond  │
 └────────┘      └─────────────┘       └──────────┘     └──────────┘     └──────────┘
  /spec /plan        /design            /build /test    /review /perf     /ship /incident
```

## Why Keystone

Agents write code quickly and erode standards quietly. The coverage gate fails,
so the threshold moves. A type error appears, so a suppression appears. A test
is inconvenient, so it is skipped. Each step is locally reasonable; the sum is a
project with a green pipeline and no standards.

Keystone gives the agent three things it otherwise lacks:

- **A procedure for each kind of work** — 31 skills, each describing what good
  looks like and ending in a verifiable exit checklist.
- **A quality bar written as numbers** — thresholds and the commands that check
  them, kept in your project rather than in the agent's memory.
- **Tripwires against erosion** — suppressions, skipped tests, weakened
  assertions and lowered thresholds stop the agent instead of turning red into
  green.

Every skill is **stack-agnostic**. None assumes a language or framework; each
starts by discovering how *this* repository actually builds, tests and ships.

## Quick start

### 1. Install

**Claude Code — from the marketplace**

```bash
/plugin marketplace add cihatcoban/keystone
/plugin install keystone@keystone-skills
```

**Claude Code — from a local clone**

```bash
git clone https://github.com/cihatcoban/keystone.git
claude --plugin-dir ./keystone
```

**Other agents** — `AGENTS.md` at the root serves Codex, Cursor, Gemini CLI,
opencode and Aider. Copy or symlink `skills/` into the directory your tool
reads. Hosts without native skill routing can wire `hooks/session-start.sh` as a
session-start hook.

### 2. Verify

In a new session, ask:

> Which skill should I use to add a new external API call?

The router should point at `distributed-systems-and-resilience` and
`api-and-contract-design`. A generic answer means the plugin is not loaded.

### 3. Set up your project

Run these inside the project you work on, not inside Keystone:

```text
/onboard        # discover the stack, write the agent's operating context
/constraints    # write CONSTRAINTS.md with real, measured numbers
```

Then work the loop:

```text
/spec → /design (only for costly-to-reverse choices) → /plan → /build → /review → /ship
```

Commands are optional — skills also trigger from how you describe the work. See
[Getting started](docs/getting-started.md) for the full walkthrough.

## How it works

| Layer | Where | Role |
|---|---|---|
| **Invariants** | `CLAUDE.md` / `AGENTS.md` | Ten non-negotiables and the bar-protection triggers that halt the agent |
| **Numbers** | `templates/CONSTRAINTS.template.md` → your project | The quality bar as a contract: thresholds plus the commands that check them |
| **Procedure** | `skills/` | How each kind of work is done well, with exit checklists |
| **Specialists** | `agents/` | Fresh-context subagents for review, architecture, security, performance and testing |

The layers rank in that order: a skill never overrides the operating contract,
your project's `CONSTRAINTS.md`, or an accepted ADR.

## Commands

| Command | Does |
|---|---|
| `/onboard` | Learn the repository and write the agent's operating context |
| `/constraints` | Establish the quality bar as an enforceable contract |
| `/spec` | Specification with measurable acceptance criteria |
| `/design` | Architecture decision, boundaries, contracts, ADR |
| `/plan` | Vertical, ordered, verifiable task breakdown |
| `/build` | Implement the next task, test first, in thin slices |
| `/test` | Design or repair the test suite |
| `/refactor` | Change structure without changing behavior |
| `/review` | Pre-merge review with a verdict |
| `/debug` | Systematic root-cause analysis |
| `/perf` | Measure-first performance work |
| `/secure` | Threat model and harden |
| `/ship` | Release readiness, rollout, rollback |
| `/incident` | Run an incident, or write the postmortem |
| `/audit` | Dependencies, licenses, personal data |

## Skills

| Phase | Skills |
|---|---|
| **Meta** | `using-skills` · `skill-authoring` · `context-engineering` · `constraint-driven-development` |
| **Define** | `requirements-interrogation` · `spec-driven-development` · `planning-and-task-breakdown` |
| **Architect** | `architecture-decisions` · `domain-modeling` · `boundaries-and-dependencies` · `api-and-contract-design` · `data-modeling-and-storage` · `distributed-systems-and-resilience` · `concurrency-and-consistency` · `frontend-architecture` |
| **Build** | `incremental-delivery` · `test-driven-development` · `testing-strategy` · `refactoring-and-simplification` · `git-workflow` |
| **Verify** | `code-review-and-quality` · `debugging-and-root-cause` · `performance-engineering` · `security-and-threat-modeling` |
| **Operate** | `observability-and-slos` · `release-engineering` · `deprecation-and-migration` · `incident-response` · `dependency-and-license-policy` · `documentation-and-knowledge` · `ai-integration-guardrails` |

**Subagents:** `architect` · `code-reviewer` · `adversarial-reviewer` ·
`test-engineer` · `security-auditor` · `performance-auditor`

Not sure where to start? `using-skills` maps a situation to the right skill and
the chain of skills around it.

## Repository layout

```text
skills/        31 skills, one directory each (SKILL.md + optional references/)
commands/      slash commands that apply a skill chain deliberately
agents/        subagent definitions
references/    checklists and catalogs the skills load on demand
templates/     CONSTRAINTS, spec, plan, ADR, design doc, runbook, postmortem
evals/         trigger cases per skill, checked statically in CI
examples/      a worked domain pack
scripts/       validators and the skill scaffolder
hooks/         optional session-start router for hosts without skill routing
docs/          getting started, principles, glossary, maturity model
```

## Quality control on the skills themselves

```bash
make all                                # structure + routing checks, same as CI
make stats                              # skill sizes
make new NAME=my-skill CAT=architect    # scaffold a new skill
```

`scripts/validate_repo.py` checks frontmatter, name/directory agreement,
description bounds, body size, exit checklists, broken links, unknown skill
references, `CLAUDE.md`/`AGENTS.md` parity and eval coverage.
`scripts/check_triggers.py` catches the two routing failures that matter: a
trigger phrase missing from a description, and two descriptions competing for
the same prompt. CI runs both — plus markdown lint and a secret scan — with no
model calls.

**VS Code:** open `keystone.code-workspace` for validation tasks, launch
configurations, snippets (`skill`, `adr`, `exit`, `table`) and a devcontainer.

## Extending

Product-specific procedure belongs in a **domain pack** in the product's own
repository; `examples/domain-pack/` is a worked example. Keystone stays
domain-neutral so it survives a change of product.

## Contributing

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) before adding
or changing a skill: a new skill must cover work no existing skill covers, ship
with an eval case, and pass `make validate`.

Report security issues privately as described in [SECURITY.md](SECURITY.md).

## License

Licensed under the [Apache License 2.0](LICENSE). See [NOTICE](NOTICE).

[license-badge]: https://img.shields.io/badge/license-Apache%202.0-blue.svg
[ci-badge]: https://github.com/cihatcoban/keystone/actions/workflows/validate.yml/badge.svg
[ci]: https://github.com/cihatcoban/keystone/actions/workflows/validate.yml
[version-badge]: https://img.shields.io/badge/version-1.0.0-informational
[skills-badge]: https://img.shields.io/badge/skills-31-success
