# Keystone

**Master-level engineering skills for AI coding agents.** Architecture-first,
stack-agnostic, from intent through operations — plus a written quality
contract the agent cannot quietly lower.

```
  DEFINE            ARCHITECT              BUILD            VERIFY           OPERATE
 ┌────────┐      ┌─────────────┐       ┌──────────┐     ┌──────────┐     ┌──────────┐
 │ intent │ ───▶ │  decision   │ ───▶  │  slice   │ ──▶ │  review  │ ──▶ │  ship    │
 │  spec  │      │ boundaries  │       │  test    │     │  debug   │     │ observe  │
 │  plan  │      │  contracts  │       │ refactor │     │ perf/sec │     │ respond  │
 └────────┘      └─────────────┘       └──────────┘     └──────────┘     └──────────┘
  /spec /plan       /design /adr        /build /test    /review /perf     /ship /incident
```

## Why this exists

Agents write code quickly and erode standards quietly. The coverage gate fails,
so the threshold moves. The type error appears, so a suppression appears. The
test is inconvenient, so it is skipped. Each step is locally reasonable; the sum
is a project with a green pipeline and no standards.

Keystone answers that with three layers:

| Layer | File | Role |
|---|---|---|
| **Invariants** | `CLAUDE.md` / `AGENTS.md` | Ten non-negotiables and the bar-protection triggers that stop the agent |
| **Numbers** | `templates/CONSTRAINTS.template.md` → your project | The quality bar as a contract, with thresholds and the commands that check them |
| **Procedure** | `skills/` | 31 skills — what good looks like for each kind of work, with exit checklists |

Everything is **stack-agnostic**: no skill assumes a language or framework, and
every skill starts from discovering how *this* repository actually works.

## Install

**Claude Code**

```bash
# local
claude --plugin-dir /path/to/keystone

# from a repository
/plugin marketplace add <owner>/keystone
/plugin install keystone@keystone-skills
```

**Other agents** — `AGENTS.md` sits at the root for Codex, Cursor, Gemini CLI,
opencode and Aider. Copy or symlink `skills/` into whatever directory your tool
reads. Hosts without native skill routing can use `hooks/session-start.sh`.

**Inside a project** — vendor it and point your plugin config at both skill
directories, so core skills and your own domain pack load together
(`examples/domain-pack/`).

## Commands

| Command | Does |
|---|---|
| `/onboard` | Learn the repository and write the agent's operating context |
| `/constraints` | Establish the quality bar as an enforceable contract |
| `/spec` | Specification with measurable acceptance criteria |
| `/design` | Architecture decision, boundaries, contracts, ADR |
| `/plan` | Vertical, ordered, verifiable task breakdown |
| `/build` | Implement the next task, test first, thin slices |
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

**Meta** — `using-skills` · `skill-authoring` · `context-engineering` ·
`constraint-driven-development`

**Define** — `requirements-interrogation` · `spec-driven-development` ·
`planning-and-task-breakdown`

**Architect** — `architecture-decisions` · `domain-modeling` ·
`boundaries-and-dependencies` · `api-and-contract-design` ·
`data-modeling-and-storage` · `distributed-systems-and-resilience` ·
`concurrency-and-consistency` · `frontend-architecture`

**Build** — `incremental-delivery` · `test-driven-development` ·
`testing-strategy` · `refactoring-and-simplification` · `git-workflow`

**Verify** — `code-review-and-quality` · `debugging-and-root-cause` ·
`performance-engineering` · `security-and-threat-modeling`

**Operate** — `observability-and-slos` · `release-engineering` ·
`deprecation-and-migration` · `incident-response` ·
`dependency-and-license-policy` · `documentation-and-knowledge` ·
`ai-integration-guardrails`

Subagents: `architect` · `code-reviewer` · `adversarial-reviewer` ·
`test-engineer` · `security-auditor` · `performance-auditor`.

## Quality control on the skills themselves

```bash
make all      # structure + routing checks, the same as CI
make stats    # skill sizes
make new NAME=my-skill CAT=architect
```

`scripts/validate_repo.py` checks frontmatter, name/directory agreement,
description bounds, body size, exit checklists, broken links, unknown skill
references, `CLAUDE.md`/`AGENTS.md` parity and eval coverage.
`scripts/check_triggers.py` catches the two routing failures that matter: a
trigger phrase missing from a description, and two descriptions competing for
the same prompt. Both run in CI with no model calls.

## VS Code

Open `keystone.code-workspace`. Tasks for validation, routing checks, markdown
lint, skill scaffolding and a combined pre-commit run; launch configurations for
the validators; snippets for `skill`, `adr`, `exit` and `table`; devcontainer
for a matching environment.

## Extending

Product-specific procedure belongs in a **domain pack** in the product's own
repository — `examples/domain-pack/` is a worked example with the rules.
Keystone stays domain-neutral so it survives a change of product.

## License

Apache License 2.0 — see `LICENSE` and `NOTICE`.
