# ADR-001: One hook dispatcher, one generated manifest per harness

- **Status:** accepted
- **Date:** 2026-10-22
- **Deciders:** Cihat
- **Reversibility:** costly — users wire hook IDs into their configuration

## Context

Keystone 1.2.0 states its invariants but enforces them only at review time.
1.3.0 adds a runtime hook layer. Three harnesses load Keystone, and each reads
hooks differently. Every fact below was checked against the loader's source on
2026-10-22 (Gemini CLI `09d81bf`, Codex `86e17e9`) or Claude Code's published
plugin reference.

| Fact | Claude Code | Codex | Gemini CLI |
|---|---|---|---|
| Reads `hooks/hooks.json` at the plugin root | always | only when the manifest names no hooks | always |
| Manifest field for other hook files | `hooks` in `.claude-plugin/plugin.json`, **merged** with the default file | `extensions.com.openai.hooks` in `plugin.json`, **replaces** the default file | none |
| Event names | `PreToolUse`, `Stop`, `PreCompact`, `SessionStart` | same as Claude Code | `BeforeTool`, `AfterAgent`, `PreCompress`, `SessionStart` |
| Unknown event name | the file fails the hooks schema | ignored silently | skipped, with a visible warning on every start |
| `permissionDecision: "ask"` | supported | rejected as invalid output | supported (`decision: "ask"`) |
| Plugin root in the hook environment | `CLAUDE_PLUGIN_ROOT` | `PLUGIN_ROOT` and `CLAUDE_PLUGIN_ROOT` | none (`${extensionPath}` only in extension files) |
| Timeout unit | seconds | seconds | milliseconds |
| Shell tool / input | `Bash` / `command` | `Bash`, `exec_command` / `command` (`cmd`) | `run_shell_command` / `command` |
| Edit tools / input | `Write`, `Edit`, `MultiEdit` / `file_path` + text | `apply_patch` / patch text in `command` | `write_file`, `replace` / `file_path` + text |

Further forces: hooks must be stdlib Python or POSIX sh (CONSTRAINTS.md), must
not assume a language, and must be switchable off one by one — a hook the user
cannot disable gets the whole plugin uninstalled.

## Decision

We will ship one dispatcher (`hooks/keystone_hook.py`) that every harness calls
with `--harness <name> --trigger <shell|edit|stop|pre-compact|session-start>`,
and generate one manifest per harness from `hooks/registry.json`. No
`hooks/hooks.json` exists, so no harness reads another harness's events.

| Harness | Manifest | How it is wired |
|---|---|---|
| Claude Code | `hooks/claude-code.json` | `hooks` in `.claude-plugin/plugin.json` — automatic |
| Codex | `hooks/codex.json` | `extensions.com.openai.hooks` in `plugin.json` — automatic, after the user trusts it |
| Gemini CLI | `hooks/gemini.json` | `scripts/install_hooks.py gemini` writes it into `.gemini/settings.json` — opt-in |

## Options considered

| Option | Fit with forces | Better at | Worse at |
|---|---|---|---|
| A (chosen): no default file, a manifest per harness, Gemini opt-in | every harness sees only its own events | correctness on all three | Gemini users run one command to enable hooks |
| B: one `hooks/hooks.json` holding Claude and Gemini events | Claude Code rejects the file over unknown events; Gemini warns on every start | zero setup | breaks the primary harness |
| C: `hooks/hooks.json` in Claude format only | Gemini warns on every start and runs the Claude `SessionStart` command with an unset path | Claude and Codex automatic | noisy and broken on Gemini |
| D: no shipped hooks, an installer for every harness | consistent | explicit consent everywhere | Claude Code users lose zero-config enforcement |

## Consequences

**Gains:** one implementation of every guard; harness differences live in one
adapter module; `make adapters-check` fails the build when a manifest drifts
from the registry.

**Costs (paid continuously):** a hook's behavior must be specified for three
output dialects; every new harness event needs a registry entry and a test.

**New constraints on future work:** hook IDs are a public interface — renaming
one breaks a user's `KEYSTONE_DISABLED_HOOKS`, so a rename is a MAJOR change.
`hooks/hooks.json` must never be added; `validate_repo.py` fails if it appears.

## The assumption most likely to be wrong

That Claude Code keeps merging manifest hook files with the default file, and
that Codex keeps reading hooks from the `com.openai` extension. Either loader
changing would show up as hooks that silently stop firing, which is why
`docs/hooks.md` lists a one-line live check per harness. Revisit when a
harness's plugin reference changes how it discovers hooks.

## Follow-up

- [x] Enforcement: `validate_repo.py` checks manifests against the registry,
  hook IDs against `docs/hooks.md`, and every invariant against a hook or a
  stated review-only reason
- [ ] Live check in each harness once the CLIs can be installed (see
  CHANGELOG 1.3.0, verification note)
