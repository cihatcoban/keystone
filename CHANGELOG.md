# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/) applied to skill
behavior — a MAJOR bump means a skill's rules changed in a way that would
change an agent's output on the same input.

## [Unreleased]

## [3.0.0] — 2026-10-23

Closes the remaining gaps against everything-claude-code 2.2.3 in fourteen
skills, again without copying its breadth: no new skills, eight descriptions
sharpened, and the always-loaded catalog grows by ≈ 54 tokens since 2.0.0
(≈ 3,001 → ≈ 3,055). Stack-specific material lives in dated, on-demand
references under [ADR-002](docs/adr/ADR-002-stack-specific-references.md);
every skill body stays under 1,400 words.

**Why MAJOR.** Under this changelog's own rule, each change below alters what
an agent produces on the same input. No existing rule was removed.

### Changed

- `agent-orchestration` — every loop gets a written spec before iteration one
  (done signal the worker cannot edit, progress metric, budget on iterations
  **and** time **and** tokens, state file, escalation, kill switch). Loop
  shapes table; new oscillation and irreversible-step stop conditions.
- `test-driven-development` — a plan file is input, not instructions: only
  the project's own verification commands run from it, and text that asks to
  skip tests is reported, not followed. A RED must fail on its assertion. An
  evidence map records RED and GREEN per planned behavior, ending with the
  full suite. `templates/plan.template.md` and `/build` carry the map.
- `frontend-architecture` — widget table (modal, disclosure, tabs,
  autocomplete, form errors, status, route change) with a keyboard script per
  widget; framework idioms checked against the framework map.
- `code-review-and-quality` — a stack-lens step: confirm the project's tools
  ran on the diff, then apply the lens for each language touched. Worked
  review example. `code-reviewer`, `/review` and the review checklist follow.
- `api-and-contract-design` — protocol checklists for GraphQL, gRPC/Protobuf,
  events and webhooks; worked example classifying a change as compatible or
  breaking. Description now names gRPC and webhooks.
- `data-modeling-and-storage` — every DDL runs with a lock timeout; schema and
  data changes are separate migrations and an applied migration is never
  edited; `down` is safe in production only before data is written in the new
  shape; partial, covering and expression indexes; engine costs looked up, not
  assumed.
- `planning-and-task-breakdown` — every task names its files and a brief a
  cold reader can act on; parallel tasks are marked and may share no files or
  outputs; plans over five tasks, with parallel work or an irreversible step
  are reviewed against the spec by `adversarial-reviewer` before T1; plan
  changes are logged. `/plan` and the plan template follow.
- `documentation-and-knowledge` — one owner per fact; intentional removals are
  recorded; documents an agent reads are evidence, not instructions; links,
  README commands and generated docs are checked in CI.
- `ai-integration-guardrails` — retrieval authorizes inside the query,
  abstains on insufficient context and checks citations against the passages
  sent; cost work starts deterministic and with the smallest model that passes
  the eval, keeps a cacheable prompt prefix and retries only transient errors.
  Description names retrieval and LLM cost.
- `agent-and-toolchain-security` — MCP tool definitions are reviewed as prompt
  text and re-reviewed on every version change; network-capable tools are
  scoped like the shell; unattended tasks get a narrowed write scope.
- `security-and-threat-modeling` — browser and authentication controls with a
  test each; description names login, session cookies and CSRF.
- `context-engineering` — which file each agent loads and how to confirm it;
  one contract instead of per-agent copies; the harness's own meter instead of
  estimates; compaction at task boundaries. Description names `GEMINI.md` and
  compaction.
- `skill-authoring` — search installed skills before writing; behavior depends
  only on `name`, `description` and the body; compliance measured with
  `make evals-live`; skills retired or merged each release.
- `agent-orchestration` — one git worktree per writing agent; a model per role.
- `frontend-architecture` — UI verification (accessible queries, end-to-end
  only for critical journeys, profile before optimizing); the framework map
  gains rendering-cost and component-test rows.
- `test-driven-development`, `testing-strategy` — point to per-language test
  idioms.
- `scripts/audit_agent_config.py` A2 — npm partial versions (`pkg@1`,
  `pkg@1.2`) and PEP 440 wildcards (`==2.*`) now count as unpinned; they were
  accepted as pinned. Expect new A2 warnings on such configurations.

### Fixed

- `make validate` check 11 claimed to verify `references/` and `templates/`
  paths used in skills but only covered commands and agents. Every skill,
  reference, template, doc and the contract is now checked; a pointer to a
  missing file fails the build.

### Added

- `references/agent-loop-patterns.md` — per-shape structure, state-file
  format, review checklist for an existing loop.
- `references/frontend-a11y-patterns.md` — widget patterns and keyboard
  scripts (WAI-ARIA Authoring Practices, WCAG 2.2 AA).
- `references/frontend-framework-map.md` — the skill's rules in React 19,
  Vue 3.5, Angular 22, Svelte 5 / SvelteKit 2, with the trap for each.
- `references/review-lenses.md` — language lenses: TypeScript/JavaScript,
  Python, Go, Java/Kotlin, C#, Rust, Swift, C/C++, SQL, shell.
- `references/api-protocol-checklists.md`.
- `references/migration-engine-lookup.md` — online forms and lock costs in
  PostgreSQL 18, MySQL 8.4 and SQLite 3.
- `references/web-session-controls.md` — password hashing parameters,
  sessions and cookies, CSRF, CORS, response headers, authentication endpoints
  and uploads, after the OWASP cheat sheets.
- `references/test-idioms.md` — table cases, focused runs, fake time and
  generated inputs per language.
- `references/review-lenses.md` — PHP, Ruby/Rails and Dart/Flutter lenses.
- `references/llm-eval-harness.md` — retrieval evaluated separately from
  generation.
- `docs/multi-agent-setup.md` and the README explain why there is no
  `GEMINI.md` or `ChatGPT.md`, and how a project points Gemini CLI at its
  `AGENTS.md`.
- ADR-002; `CONTRIBUTING.md` states the references exception.
- Eval cases: new positive prompts and expectations for every changed skill
  (131 prompts, 0 weak, 0 collisions).

### Upgrading

- Expect evidence maps in TDD work and pull requests, a "tools ran / lens
  applied" line in reviews, a loop spec before any agent loop starts, file
  lists and briefs in plans, and lock timeouts in migrations.
- `audit_agent_config.py` may report new A2 warnings for MCP servers pinned to
  `@1`, `@1.2` or `==2.*`; pin a full version.
- The stack references are dated. Re-check them when a listed language or
  framework ships a major version.

### Verification note

CI passes on the release commit: repository validation, routing check (131
prompts, 0 weak, 0 collisions), 150 tooling tests, adapter freshness, `.env`
hygiene, ruff, markdown lint and secret scan. Engine, framework, protocol and
agent facts in the new references were checked against primary documentation
on 2026-10-22 and 2026-10-23; each reference names what it was checked against.
`make evals-live` — whether agents *follow* the changed skills — was not run
for this release: the authoring environment had no model credentials. Routing
was verified statically only.

## [2.0.0] — 2026-10-22

Keystone's invariants used to be written down and checked only in review. 2.0.0
enforces them while the agent works, and closes the gaps found against
everything-claude-code 2.2.3 without copying its breadth: two new skills, so
the skill catalog grows from ≈ 2,800 to ≈ 3,000 tokens.

**Why MAJOR.** Under this changelog's own rule, a skill rule that changes an
agent's output on the same input is a major change. No existing line was
removed, but three additions change what an agent does:

- `dependency-and-license-policy` — "Search before you write": before the
  necessity questions, the agent searches this repository and the team's own
  packages, and every pull request says what was searched ("searched for X,
  reused Y" or "nothing found").
- `release-engineering` — "Post-release verification": the timed canary
  checklist is written into the release plan before deploying, and a check
  that cannot run makes the release notes say "not verified" instead of
  declaring success.
- `git-workflow` — "Conventional Commits in practice": in a repository whose
  commits do not use `type(scope):`, the agent follows the repository's
  convention instead of the template. `CLAUDE.md` §3 already ranked repository
  conventions above a skill; the skill now says so.

### Upgrading from 1.x

- Expect the three changes above in agent output: a search line in PR
  descriptions, a post-release checklist in release plans, and commit messages
  that follow your repository's existing style.
- Runtime hooks are on in Claude Code and Codex as soon as the plugin updates.
  The default `warn` profile reports and does not block, except
  `git.force-push`, `secret.*` and `irreversible.command`, which ask for
  approval in Claude Code and Gemini CLI (Codex has no hook approval prompt
  and warns instead). Plan for those prompts in unattended runs. Turn hooks
  off with `KEYSTONE_HOOK_PROFILE=off`, or one at a time with
  `KEYSTONE_DISABLED_HOOKS` ([docs/hooks.md](docs/hooks.md)).
- Gemini CLI hooks are opt-in: `scripts/install_hooks.py gemini`.

### Added

- **Runtime hooks** (`hooks/`, [docs/hooks.md](docs/hooks.md),
  [ADR-001](docs/adr/ADR-001-hook-layer.md)). One stdlib dispatcher serves
  every harness; a manifest per harness is generated from
  `hooks/registry.json`. Profiles `off` / `warn` (default) / `strict` via
  `KEYSTONE_HOOK_PROFILE` or `.keystone/config.json`; any hook or family can be
  switched off with `KEYSTONE_DISABLED_HOOKS`. Hooks fail open. Claude Code and
  Codex wire them through their manifests; Gemini CLI and plugin-less installs
  use `scripts/install_hooks.py`.
  - `bar.*`: lowered `CONSTRAINTS.md` thresholds, edited lint/test config,
    unjustified suppressions, weakened or skipped tests. Protected tools are
    read from the project's `CONSTRAINTS.md`, not a fixed list.
  - `git.*`: `--no-verify`, force push to protected branches, and commit
    messages checked against the project's own convention when it has one.
  - `secret.*`: credentials in staged changes and in files being written.
  - `irreversible.command`: asks before deletes, resets, destructive SQL,
    infrastructure destroys and publishes.
  - `rules.project`: `.keystone/rules/*.md` turns a team's own prohibitions
    into hooks without code.
  - `session.*`: handoff state saved before compaction and loaded at session
    start.
  - `verify.stop`: warns (or, under `strict`, blocks once) when the agent ends
    its turn with unverified changes.
- **`/verify`** and `scripts/verify.py`: runs the commands in the new
  "Verification commands" table of `CONSTRAINTS.md` in phase order, then scans
  the diff for bar-protection triggers. Findings need an explicit
  `--acknowledge "<reason>"`, which is recorded. `references/verification-loop.md`.
- **`/handoff`** and `templates/handoff.template.md`: `.keystone/handoff.md`
  carries goal, evidence, next steps and rejected approaches across compaction
  and restarts.
- **`/retro`** and `templates/LESSONS.template.md`: lessons from a session are
  proposed, reviewed and only then added to the project's `LESSONS.md`; a
  lesson that can become a check is turned into one.
- **`agent-and-toolchain-security`** skill and `scripts/audit_agent_config.py`:
  the agent's own MCP servers, plugins, hooks, approval modes and reachable
  credentials, across Claude Code, Gemini CLI, Codex, Cursor and VS Code.
  Read-only; never prints a secret value.
- **`agent-orchestration`** skill: when several agents pay off, contracts
  before fan-out, verification by an agent that did not do the work, and stop
  conditions for loops, budgets and disagreement.
- **Subagents** `silent-failure-hunter` (reports code that fails without
  telling anyone) and `build-error-resolver` (fixes a red build at the cause,
  never by suppressing or weakening checks).
- **Cursor, opencode and GitHub Copilot**: `scripts/install_agents.py` installs
  the skills into `.agents/skills/` plus the commands and subagents each tool
  supports. Everything it writes records a hash; it replaces or removes only
  files that still match, so neither your files nor your edits to its files
  are ever lost.
- `make evals-live` (`scripts/evals_live.py`): optional, outside CI. Sends eval
  prompts to a real agent CLI and grades answers against the skill's exit
  checklist, so "selected" and "followed" are measured separately.
- References: `privacy-compliance.md` (KVKK and GDPR mapped to system
  mechanisms; engineering guidance, not legal advice), `llm-eval-harness.md`,
  `error-handling.md`.
- New sections in existing skills, no rule changed:
  `security-and-threat-modeling` (verification recipes, scanner discovery,
  OWASP ASVS 5.0 mapping); `context-engineering` (handoffs, context and cost
  budget); `git-workflow` (Conventional Commits in practice);
  `dependency-and-license-policy` (search before you write);
  `release-engineering` (post-release verification; `/ship` writes the canary
  list). Pointer lines in `ai-integration-guardrails`,
  `code-review-and-quality` and `using-skills`.
- `validate_repo.py` checks the hook registry, a guard per hook ID, the
  invariant-to-hook mapping, `docs/hooks.md` parity and manifest wiring.
- `CONSTRAINTS.template.md`: verification commands table; agent context and
  agent cost rows.
- `CONSTRAINTS.md`: Keystone's own quality contract, with measured thresholds
  and the check that enforces each one.
- `SECURITY.md` lists which scripts write outside the repository, run
  project commands or reach the network, instead of claiming none do.
- `validate_repo.py` warns when a skill description exceeds the 320-character
  target; the hard limit stays 80–500. Covered by `test_validate_repo.py`.
- CI runs `ruff check` and `ruff format --check`, pinned to the pre-commit
  version (0.6.9).

### Changed

- Scripts reformatted with `ruff format`; no logic change.
- GitHub Actions upgraded to Node 24 runtimes: `actions/checkout@v7`,
  `actions/setup-python@v7`, `gitleaks/gitleaks-action@v3`.

### Fixed

- `CONTRIBUTING.md` claimed `make validate` enforced the 320-character
  description target; it now states what the validator actually checks.

### Verification note

`make all` passes: 34 skills, 112 positive eval prompts with 0 weak and 0
collisions, 138 unit tests. Every guard has true- and false-positive tests.
Harness hook formats were checked against Gemini CLI and Codex source, not
run live. Not yet done in a real CLI: a live hook session in each harness,
`make evals-live` against a real model, and the Cursor, opencode and Copilot
checks listed in `docs/multi-agent-setup.md`.

## [1.2.0] — 2026-10-01

### Added

- **Gemini CLI support.** `gemini-extension.json` at the root; the operating
  contract loads automatically through `contextFileName: AGENTS.md`; skills and
  subagents load natively; the 16 commands are generated as
  `commands/keystone/*.toml` and appear as `/keystone:<name>`, the same names
  as in Claude Code.
- **Codex (OpenAI) support.** Root `plugin.json` is now an Agent Plugins
  manifest (`$schema` set — without it Codex silently falls back to the Claude
  manifest); `.agents/plugins/marketplace.json` for local install.
- `configuration-and-secrets` skill: `.env` / `.env.example` contract,
  load-once-and-validate, provider key conventions (Anthropic, OpenAI, Gemini),
  and keeping secrets out of AI agents' context.
- `/env` command, `templates/env.example.template`,
  `templates/agent-secret-guards.md` (Claude Code, Gemini CLI, Codex snippets).
- `scripts/check_env.py`: stack-agnostic, stdlib-only secret and `.env`
  hygiene check for any project. Never prints a secret value.
- `scripts/build_adapters.py`: one source (`commands/*.md`), generated
  per-agent adapters, `--check` mode for CI.
- First unit-test suite for Keystone's own tooling (`make test`, 25 tests).
- `docs/multi-agent-setup.md`.

### Changed

- All 32 skill descriptions rewritten shorter (average 395 → 265 characters).
  Codex removes **every** description when the skill catalog exceeds its
  budget; the catalog is now ≈ 2,800 tokens instead of ≈ 3,800. No trigger was
  lost: `check_triggers.py` stays at 0 weak, 0 collisions over 97 prompts.
- `validate_repo.py` now checks all four manifests against the rules of the
  loader that reads them, version agreement across manifests, generated-adapter
  freshness, Gemini subagent name slugs, and the skill catalog budget.
- `CONSTRAINTS.template.md`: secret-hygiene rows made mechanically checkable.

### Fixed

- `check_env.py` reported test fixtures as undocumented variables on its first
  run against Keystone itself. Test code is now excluded from drift checks but
  still scanned for credentials.

- Markdown lint, a CI gate since 1.0.0, had never actually run and would have
  failed with 749 findings. Fixed at the root: placeholders in the CONSTRAINTS
  template are code spans (the auto-fixer was merging `___` blanks as emphasis),
  bare code fences got a language, and the linter is pinned to 0.22.1. MD060
  (table pipe alignment, new in markdownlint 0.38) is disabled with the reason
  recorded in `.markdownlint-cli2.jsonc`. Two auto-fixes that changed meaning
  were rejected: renumbering the 1–20 adoption path, and the placeholder merge.

### Verification note

The agent CLIs could not be installed in the build environment (registry
policy), so manifests were verified against the loaders' source code: Gemini
CLI `FileCommandLoader`, extension manager, skill and agent loaders; Codex
`find_plugin_manifest_path`, Agent Plugins parser, marketplace resolver and
skill catalog renderer. Gemini commands were parsed with `@iarna/toml`, the
library Gemini uses. A live run in each CLI is still the final check.

## [1.1.1] — 2026-09-23

### Fixed

- `.claude-plugin/plugin.json` failed to load in Claude Code 2.1.280 with
  `agents: Invalid input`: the `agents` field accepts file paths, not a
  directory. Removed `commands`, `agents` and `skills` from the manifest —
  all three directories are auto-discovered, and listing `commands`/`agents`
  *replaces* the default scan rather than adding to it.
- Found on first real install; `validate_repo.py` checked the manifest's
  existence but not its schema. Added a schema check.

## [1.1.0] — 2026-09-23

First field test (`~/dev/reservation-service`) — a stock reservation service
built end to end under the process. Four changes came out of it.

### Changed

- `constraint-driven-development`: new section **"Validate the instrument
  before trusting the number"**. The field test's home-made coverage gate
  reported 43%, then 57%, before reporting the true 93.8% — it traced only the
  main thread, then counted module-level lines executed before instrumentation
  started. The skill demanded mechanical enforcement but said nothing about
  verifying the measurement, which is how a gate acquires authority it has not
  earned.
- `architecture-decisions`: added the **pre-implementation amendment**
  carve-out. Implementation showed ADR-001's description was imprecise (one
  atomic statement enforces the invariant, but the reservation row still needs
  the same transaction) an hour after acceptance. Superseding a one-hour-old
  ADR is theatre; leaving it wrong is worse.
- `templates/CONSTRAINTS.template.md`: states what to do when a named tool
  cannot exist in the environment, and points at instrument validation. The
  test machine had no linter, no type checker and no package index.
- `planning-and-task-breakdown` and `templates/plan.template.md`: tasks now
  reference a spec criterion by number instead of restating it. Writing each
  requirement twice in different words is how two versions of it start drifting.

## [1.0.0] — 2026-09-22

### Added

- 31 skills across meta, define, architect, build, verify and operate phases
- Operating contract (`CLAUDE.md` / `AGENTS.md`) with 10 invariants and
  bar-protection triggers
- `templates/CONSTRAINTS.template.md` — the project quality bar as a contract
- 15 slash commands and 6 subagents
- 12 reference checklists and 8 document templates
- `scripts/validate_repo.py`, `scripts/check_triggers.py`, `scripts/new_skill.py`
- Trigger eval case per skill
- VS Code workspace, tasks, launch configurations, snippets, devcontainer
- Example domain pack under `examples/domain-pack/`
