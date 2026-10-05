# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/) applied to skill
behavior — a MAJOR bump means a skill's rules changed in a way that would
change an agent's output on the same input.

## [1.0.0] — 2026-09-22

### Added
- 31 skills across meta, define, architect, build, verify and operate phases
- Operating contract (`CLAUDE.md` / `AGENTS.md`) with 10 invariants and
  bar-protection triggers
- `templates/CONSTRAINTS.template.md` — the project quality bar as a contract
- 13 slash commands and 6 subagents
- 12 reference checklists and 8 document templates
- `scripts/validate_repo.py`, `scripts/check_triggers.py`, `scripts/new_skill.py`
- Trigger eval case per skill
- VS Code workspace, tasks, launch configurations, snippets, devcontainer
- Example domain pack under `examples/domain-pack/`
