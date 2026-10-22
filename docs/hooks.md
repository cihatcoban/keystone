# Runtime hooks

Keystone's invariants (`CLAUDE.md` §1) used to be enforced only when someone
read a diff. From 1.3.0 the agent's own harness checks them as the agent works:
before a shell command runs, before a file is written, when the agent ends its
turn, and around context compaction. Why the layer is built this way, and the
harness facts it rests on, are in [ADR-001](adr/ADR-001-hook-layer.md).

## Profiles

| Profile | What happens on a finding |
|---|---|
| `off` | Nothing runs |
| `warn` (default) | The agent and the user see a message; nothing is blocked. Hooks marked *ask* request your approval |
| `strict` | Findings block the action and tell the agent why |

Set the profile per project in `.keystone/config.json`, or per shell with
`KEYSTONE_HOOK_PROFILE=strict`. The environment wins over the file.

## Switching hooks off

Every hook has a stable ID. Disable one, or a whole family, without touching
the others:

```bash
export KEYSTONE_DISABLED_HOOKS="git.commit-message,secret.*"
```

or in `.keystone/config.json`:

```json
{
  "profile": "warn",
  "disabled_hooks": ["git.commit-message"],
  "protected_branches": ["main", "release/*"],
  "protected_paths": ["config/eslint/**"],
  "commit_convention": "auto"
}
```

| Key | Default | Meaning |
|---|---|---|
| `profile` | `warn` | `off`, `warn` or `strict` |
| `disabled_hooks` | `[]` | Hook IDs, families (`secret`) or globs (`bar.*`) |
| `protected_branches` | `main`, `master`, `trunk`, `develop`, `production`, `prod`, `release/*`, `release-*` | Branches a force push must not rewrite |
| `protected_paths` | `[]` | Globs treated as quality-check configuration |
| `commit_convention` | `auto` | `conventional`, `none`, or `auto`: detect from commitlint config or recent history |

Hook IDs are a public interface: renaming one is a MAJOR version change.

## Setup per harness

| Harness | How the hooks load | One-line live check |
|---|---|---|
| Claude Code | Automatically with the plugin, through `hooks` in `.claude-plugin/plugin.json` | `/hooks` lists entries whose command contains `keystone` |
| Codex | Automatically with the plugin, through `extensions.com.openai.hooks` in `plugin.json`; Codex runs them after you trust them in `/hooks` | `/hooks` lists them as trusted |
| Gemini CLI | Opt-in: `python3 ~/.gemini/extensions/keystone/scripts/install_hooks.py gemini` in the project | `/hooks` lists the `keystone-*` hooks |
| Without the plugin | `python3 <keystone>/scripts/install_hooks.py <claude-code\|codex\|gemini>` | as above |

Gemini needs the extra step because it reads `hooks/hooks.json` from every
extension and warns about event names it does not know; Keystone therefore
ships no such file. `install_hooks.py --uninstall` removes exactly what it
added and keeps a `.bak` of the previous settings.

## Hook reference

Action columns show what each profile does with a finding. *ask* asks for your
approval in Claude Code and Gemini CLI; Codex has no approval prompt for hooks,
so there *ask* becomes a warning under `warn` and a block under `strict`.

| ID | Trigger | Invariants | `warn` | `strict` | Fires when |
|---|---|---|---|---|---|
| `bar.constraints-lowered` | edit | 4, 5 | warn | block | A threshold in `CONSTRAINTS.md` moves in the permissive direction, a row is removed, or the file is deleted |
| `bar.check-config` | edit | 5 | warn | block | A config file of a tool named in `CONSTRAINTS.md` (its "Measured by" column or verification commands), or a `protected_paths` match, is edited |
| `bar.suppression` | edit | 5 | warn | block | A new lint or type suppression has no tracking link on the same line; documentation files are exempt |
| `bar.test-weakened` | edit, shell | 5 | warn | block | A test gets a skip or focus marker, loses tests or assertions, or a test file is deleted |
| `git.no-verify` | shell | 5 | warn | block | `--no-verify`, `git commit -n`, `core.hooksPath`, `HUSKY=0` or `SKIP=` on a git command that runs hooks |
| `git.force-push` | shell | 3 | ask | block | A force push, `+refspec`, `--mirror` or remote delete targets a protected branch |
| `secret.staged` | shell | 8 | ask | block | `git commit` would record a credential-shaped string (patterns shared with `check_env.py`) |
| `secret.write` | edit | 8 | ask | block | A file write adds a credential-shaped string; lines marked `keystone:allow-secret` are exempt |
| `irreversible.command` | shell | 3 | ask | ask | A recursive delete outside build output, `git reset --hard`, `git clean -f`, destructive SQL, infrastructure destroy, or a publish |
| `rules.project` | edit, shell | — | rule | rule | A rule in `.keystone/rules/*.md` matches; the rule sets its own action |

## Project rules

A team turns its own prohibitions into hooks without writing code: one markdown
file per rule in `.keystone/rules/`.

```markdown
---
name: no-raw-sql
trigger: edit                 # shell | edit | any
pattern: \bdb\.raw\(
paths: src/**, !src/db/**     # edit only; '!' excludes
action: block                 # warn | ask | block (default warn)
---
Raw SQL bypasses the repository layer. Use the query builder in src/db.
```

The pattern is a Python regular expression, matched against the lines an edit
adds or against a shell command. A rule is the team's explicit decision, so its
action holds under both `warn` and `strict`; `off` and
`KEYSTONE_DISABLED_HOOKS=rules.project/no-raw-sql` switch it off. A rule that
does not parse is skipped and reported, never applied halfway.

## Invariants and their enforcement

Every invariant maps to at least one hook or to a stated reason that only a
reviewer can judge it. `make validate` fails when one has neither.

| Invariant | Enforced by |
|---|---|
| 1. Evidence over assertion | review only — not enforced at runtime yet |
| 2. Discover, don't assume | review only — no tool call shows whether a command was found or invented |
| 3. Reversibility first | `git.force-push`, `irreversible.command` |
| 4. The quality bar is written | `bar.constraints-lowered` |
| 5. Never lower the bar | `bar.*`, `git.no-verify` |
| 6. One logical change per commit | review only — not enforced at runtime yet |
| 7. Boundaries are real | review only — mechanical checks arrive with the 1.4.0 traceability graph |
| 8. Security and privacy | `secret.staged`, `secret.write` |
| 9. An AI model is never the decision maker | review only — a property of the design, judged in review |
| 10. Say what you did not do | review only — not enforced at runtime yet |

## How a hook behaves

- **Fails open.** A guard that crashes is skipped; it never turns into a block.
  Set `KEYSTONE_HOOK_DEBUG=1` to see why on stderr.
- **No network, no writes outside `.keystone/`.** Guards read the repository
  and run read-only `git` commands.
- **One process per event.** The dispatcher runs every guard for a trigger in
  one Python process: about 0.1 s per call, measured on Linux with a commit
  command (which also reads the staged diff).
- **No Python, no hooks.** `hooks/run.sh` exits quietly when no Python 3.9+ is
  on `PATH`.
- **Codex on Windows** runs hook commands through `cmd.exe`, which cannot
  expand `${PLUGIN_ROOT}`; use `install_hooks.py codex` there instead.

## Writing a new hook

1. Add the entry to `hooks/registry.json`: ID, triggers, invariants, the action
   under `warn` and `strict`, one-line summary.
2. Implement the guard in a `hooks/keystone_hooks/guards_*.py` module and list
   it in that module's `GUARDS`.
3. Add a row to the Hook reference table above, and a false-positive test next
   to the true-positive one in `scripts/tests/`.
4. `make adapters` regenerates the three manifests; `make all` must pass.
