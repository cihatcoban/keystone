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
[How it works](#how-it-works) · [Runtime hooks](docs/hooks.md) ·
[Changelog](CHANGELOG.md) · [Contributing](CONTRIBUTING.md)

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

- **A procedure for each kind of work** — 34 skills, each describing what good
  looks like and ending in a verifiable exit checklist.
- **A quality bar written as numbers** — thresholds and the commands that check
  them, kept in your project rather than in the agent's memory.
- **Tripwires against erosion** — suppressions, skipped tests, weakened
  assertions and lowered thresholds stop the agent instead of turning red into
  green. Runtime hooks catch them as the agent works, not only in review
  ([Runtime hooks](docs/hooks.md)).

Every skill is **stack-agnostic**. None assumes a language or framework; each
starts by discovering how *this* repository actually builds, tests and ships.
Where the language, framework, engine or protocol matters — review traps,
framework idioms, migration locks, GraphQL or gRPC rules — the skill points to
a dated lookup in `references/`, loaded only after stack discovery
([ADR-002](docs/adr/ADR-002-stack-specific-references.md)). The always-loaded
part stays small: the 34 skill descriptions are ≈ 3,050 tokens.

## Quick start

### 1. Install

One repository, six agents. Skills, the operating contract and the subagents
are shared; each agent gets the manifest or install layout its own loader
expects. The scripts and runtime hooks need Python 3.9 or later and nothing
else; without Python the skills still work and the hooks stay silent.

Upgrading from 1.x? 2.0.0 changes three skills' output and adds runtime hooks;
see [Upgrading from 1.x](CHANGELOG.md#200--2026-10-22).

**Claude Code** — from the marketplace:

```bash
/plugin marketplace add cihatcoban/keystone
/plugin install keystone@keystone-skills
```

**Gemini CLI** — as an extension:

```bash
gemini extensions install https://github.com/cihatcoban/keystone
```

**Codex (ChatGPT)** — as a plugin marketplace:

```bash
codex plugin marketplace add cihatcoban/keystone    # then enable it in /plugins
```

**From a local clone** — any of the three:

```bash
git clone https://github.com/cihatcoban/keystone.git
claude --plugin-dir ./keystone
gemini extensions link ./keystone
codex plugin marketplace add ./keystone
```

In Claude Code and Gemini CLI the commands are namespaced: `/keystone:review`,
`/keystone:spec` and so on. Codex has no plugin commands; invoke the skill
directly, for example `$code-review-and-quality`. The full guide is
[Multi-agent setup](docs/multi-agent-setup.md).

**Cursor, opencode, GitHub Copilot** — installed into the project's
`.agents/skills/`, with the commands and subagents each tool supports:

```bash
python3 ./keystone/scripts/install_agents.py opencode   # or cursor, copilot
```

**Other agents** (Aider and the like) — `AGENTS.md` sits at the root. Copy or
symlink `skills/` into the directory your tool reads. Hosts without native
skill routing can wire `hooks/session-start.sh` as a session-start hook.

**Runtime hooks** — on in Claude Code with the plugin, and in Codex once you
trust them in `/hooks`. Gemini CLI is opt-in:
`python3 ~/.gemini/extensions/keystone/scripts/install_hooks.py gemini` inside
the project. Cursor, opencode and Copilot have no Keystone hooks yet. The
default `warn` profile reports and does not block, except force pushes to
protected branches, credentials and irreversible commands, which ask first:

```bash
export KEYSTONE_HOOK_PROFILE=strict                  # block instead of warn; off disables all
export KEYSTONE_DISABLED_HOOKS="git.commit-message"  # switch off one hook or family
```

Per-project settings live in `.keystone/config.json`; see
[Runtime hooks](docs/hooks.md).

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
/spec → /design (only for costly-to-reverse choices) → /plan → /build → /verify → /review → /ship
```

Commands are optional — skills also trigger from how you describe the work. See
[Getting started](docs/getting-started.md) for the full walkthrough.

## How it works

| Layer | Where | Role |
|---|---|---|
| **Invariants** | `CLAUDE.md` / `AGENTS.md` | Ten non-negotiables and the bar-protection triggers that halt the agent |
| **Numbers** | `templates/CONSTRAINTS.template.md` → your project | The quality bar as a contract: thresholds plus the commands that check them |
| **Procedure** | `skills/` | How each kind of work is done well, with exit checklists |
| **Specialists** | `agents/` | Fresh-context subagents for review, architecture, security, performance, testing, silent failures and red builds |
| **Enforcement** | `hooks/` | Runtime guards for the invariants, with `off` / `warn` / `strict` profiles and per-hook switches |

The layers rank in that order: a skill never overrides the operating contract,
your project's `CONSTRAINTS.md`, or an accepted ADR.

### One contract, every agent

The operating contract is one text under two names, kept byte-identical by
`make validate`:

| Agent | Reads | Check with |
|---|---|---|
| Claude Code | `CLAUDE.md` (`AGENTS.md` only when no `CLAUDE.md` exists) | `/context` |
| Codex (OpenAI, also in ChatGPT) | `AGENTS.md` | `/status` |
| Gemini CLI | `AGENTS.md`, named by `contextFileName` in `gemini-extension.json` | `/memory show` |

There is no `GEMINI.md` and no `ChatGPT.md` on purpose: no agent reads a
`ChatGPT.md`, and a third copy of the contract would drift. In your own project,
point Gemini CLI at `AGENTS.md` with `context.fileName` — see
[Multi-agent setup](docs/multi-agent-setup.md#the-operating-contract-in-your-own-projects).

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
| `/env` | `.env` hygiene, config drift, agent access to secrets, provider keys |
| `/verify` | Run the project's verification commands in phase order and scan the diff for bar-protection triggers |
| `/handoff` | Write `.keystone/handoff.md` so the next session or compaction continues the work |
| `/retro` | Turn what a session learned into reviewed `LESSONS.md` entries |

## Skills

| Phase | Skills |
|---|---|
| **Meta** | `using-skills` · `skill-authoring` · `context-engineering` · `constraint-driven-development` · `agent-orchestration` |
| **Define** | `requirements-interrogation` · `spec-driven-development` · `planning-and-task-breakdown` |
| **Architect** | `architecture-decisions` · `domain-modeling` · `boundaries-and-dependencies` · `api-and-contract-design` · `data-modeling-and-storage` · `distributed-systems-and-resilience` · `concurrency-and-consistency` · `frontend-architecture` |
| **Build** | `incremental-delivery` · `test-driven-development` · `testing-strategy` · `refactoring-and-simplification` · `git-workflow` |
| **Verify** | `code-review-and-quality` · `debugging-and-root-cause` · `performance-engineering` · `security-and-threat-modeling` · `agent-and-toolchain-security` |
| **Operate** | `observability-and-slos` · `release-engineering` · `configuration-and-secrets` · `deprecation-and-migration` · `incident-response` · `dependency-and-license-policy` · `documentation-and-knowledge` · `ai-integration-guardrails` |

**Subagents:** `architect` · `code-reviewer` · `adversarial-reviewer` ·
`test-engineer` · `security-auditor` · `performance-auditor` ·
`silent-failure-hunter` · `build-error-resolver`

Not sure where to start? `using-skills` maps a situation to the right skill and
the chain of skills around it.

## Repository layout

```text
skills/        34 skills, one directory each (SKILL.md)
commands/      slash commands that apply a skill chain deliberately
agents/        subagent definitions
references/    checklists, catalogs and dated stack lookups the skills load
               on demand
templates/     CONSTRAINTS, spec, plan, ADR, design doc, runbook, postmortem,
               handoff, lessons
evals/         trigger cases per skill, checked statically in CI
examples/      a worked domain pack
scripts/       validators, adapter generator, env check, /verify runner, agent
               config audit, hook and agent installers, skill scaffolder
hooks/         runtime guards (one stdlib dispatcher, a manifest per harness)
docs/          getting started, multi-agent setup, hooks, ADRs, principles
```

## Quality control on the skills themselves

```bash
make all                                # what CI runs, except ruff, markdown lint and secret scan
make lint                               # markdown lint, pinned version
make stats                              # skill sizes
make new NAME=my-skill CAT=architect    # scaffold a new skill
make evals-live ARGS="--cli claude"     # optional: is each skill followed, not only selected (calls a model)
```

`scripts/validate_repo.py` checks frontmatter, name/directory agreement,
description bounds, body size, exit checklists, broken links, unknown skill
references, pointers to `references/` and `templates/` files,
`CLAUDE.md`/`AGENTS.md` parity, eval coverage, the skill catalog
budget, every manifest against its loader's rules and their version agreement,
generated adapters, and the hook registry (a guard per hook ID, every
invariant mapped to a hook, `docs/hooks.md` in sync).
`scripts/check_triggers.py` catches the two routing failures that matter: a
trigger phrase missing from a description, and two descriptions competing for
the same prompt. CI runs both, plus the unit tests, adapter freshness, `.env`
hygiene, ruff, markdown lint and a secret scan — with no model calls.

`scripts/build_adapters.py` generates the Gemini CLI commands from
`commands/*.md`; `--check` fails CI when they drift. `scripts/check_env.py` is a
stack-agnostic, standard-library-only secret and `.env` hygiene check you can
run in **any** project: `python3 path/to/keystone/scripts/check_env.py`.
`scripts/audit_agent_config.py` checks the agents' own configuration —
approval modes, MCP servers, hooks, credentials — the same way. Keystone's own
tooling has a unit-test suite: `make test`.

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
[version-badge]: https://img.shields.io/badge/version-2.0.0-informational
[skills-badge]: https://img.shields.io/badge/skills-34-success
