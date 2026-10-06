# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/) applied to skill
behavior — a MAJOR bump means a skill's rules changed in a way that would
change an agent's output on the same input.

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
