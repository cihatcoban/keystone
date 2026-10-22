# Security Policy

## Scope

This repository contains process documentation and tooling scripts. It holds
no production code and no credentials. The security surface is:

- `scripts/*.py` — run locally and in CI
- `hooks/` — runtime guards the agent's harness runs on shell commands, file
  writes, turn end and compaction (`docs/hooks.md`); stdlib only, fail open
- Anything a consumer copies out of `templates/`

## Reporting

Report a suspected issue privately to the repository owner. Do not open a
public issue for anything exploitable.

## Guarantees this repository tries to keep

- No secret values anywhere, including examples. `.env.example` files list key
  names only.
- Validators, checks and audits (`validate_repo.py`, `check_triggers.py`,
  `check_env.py`, `audit_agent_config.py`, `build_adapters.py`) read files and
  print findings or write only inside this repository. They do not execute
  repository content or make network calls.
- These scripts go further, by design, and only when you run them:
  - `install_agents.py` and `install_hooks.py` write into the project you
    name and, with `--scope user` or for Gemini CLI, into your home
    directory. They never overwrite or delete a file they did not write, or
    one you have edited since.
  - `verify.py` runs the commands listed in that project's `CONSTRAINTS.md`.
    Commands it only infers run after you confirm them (`--inferred`).
  - `evals_live.py` drives an agent CLI, which calls a model over the
    network. It is never run in CI.
- Hooks write only under the project's `.keystone/state/` and never make
  network calls.
- CI runs a secret scanner on every pull request.

## For projects that install Keystone

The `security-and-threat-modeling` skill and
`references/threat-model-checklist.md` define the expected practice. Keystone
does not grant your project any security property by itself — it describes the
work that does.
