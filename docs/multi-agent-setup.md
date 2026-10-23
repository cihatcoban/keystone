# Multi-agent setup — Claude Code, Gemini CLI, Codex, Cursor, opencode, Copilot

Keystone is one source of truth packaged three ways. The skills, the operating
contract and the subagents are shared; each agent gets the manifest its loader
expects. Nothing is maintained twice by hand.

## What each agent gets

| | Claude Code | Gemini CLI | Codex (ChatGPT) |
|---|---|---|---|
| Manifest | `.claude-plugin/plugin.json` | `gemini-extension.json` | `plugin.json` (Agent Plugins schema) |
| 34 skills (`skills/*/SKILL.md`) | native | native | native |
| Operating contract | via the project's `CLAUDE.md` | **loaded automatically** (`contextFileName: AGENTS.md`) | via the project's `AGENTS.md` |
| 19 commands | `/keystone:<name>` from `commands/*.md` | `/keystone:<name>` from generated `commands/keystone/*.toml` | no plugin commands — invoke the skill: `$code-review-and-quality` |
| 8 subagents (`agents/*.md`) | native | native | not supported by Codex plugins |
| Runtime hooks (`docs/hooks.md`) | automatic, from `hooks/claude-code.json` | opt-in: `scripts/install_hooks.py gemini` | automatic, from `hooks/codex.json`, after you trust them in `/hooks` |
| Local install | `--plugin-dir` | `gemini extensions link` | `.agents/plugins/marketplace.json` |

Every manifest carries the same version. `make validate` fails if they diverge,
if a manifest has a shape its agent rejects, or if a generated Gemini command
is out of date.

## Claude Code

```bash
claude plugin validate ~/dev/keystone        # must pass
claude --plugin-dir ~/dev/keystone           # this session only
```

Check: `/plugin` → **Errors (0)**; type `/keystone:` and the 19 commands appear;
`/hooks` lists the Keystone hooks.

## Gemini CLI

```bash
npm install -g @google/gemini-cli            # or: brew install gemini-cli
gemini extensions link ~/dev/keystone        # symlink: edits are live
gemini extensions list                       # keystone should be listed
```

Inside a session:

- `/keystone:review`, `/keystone:spec` … — same names as in Claude Code.
  Gemini renames an extension command only if it collides with another one.
- `/skills` lists the 34 skills; Gemini activates them on demand and asks
  before loading one.
- `AGENTS.md` is loaded as context for every session with the extension
  enabled, so the invariants and bar-protection rules apply without setup.

Agent Skills and subagents are enabled by default in Gemini CLI. If either was
turned off in `settings.json` (`skills.enabled`, `experimental.enableAgents`),
turn it back on.

`gemini extensions install ~/dev/keystone` also works; it copies instead of
linking, so you reinstall after every Keystone update.

## Codex (OpenAI / ChatGPT)

```bash
npm install -g @openai/codex                 # or: brew install codex
codex plugin marketplace add ~/dev/keystone  # reads .agents/plugins/marketplace.json
```

Then open `/plugins` in a session and install **keystone**. Codex reads the root
`plugin.json`, which declares the Agent Plugins `$schema` — without that field
Codex would ignore it and fall back to the Claude manifest.

Using skills in Codex:

- Implicitly: describe the work; Codex picks matching skills from their
  descriptions.
- Explicitly: `$spec-driven-development`, `$code-review-and-quality` …, or the
  `/skills` picker. This replaces the slash commands Codex plugins cannot ship.

Simpler alternative, no plugin: link the skills where Codex already looks.

```bash
mkdir -p ~/.agents/skills
ln -s ~/dev/keystone/skills/* ~/.agents/skills/      # every project
# or, per project:   mkdir -p .agents/skills && ln -s ~/dev/keystone/skills/* .agents/skills/
```

### The skill catalog budget

Codex injects every skill's name and description into each session, within a
budget of 2% of the model's context window (8,000 characters when the window is
unknown). **When the catalog exceeds the budget, Codex removes all descriptions
at once**, and implicit routing stops working.

Keystone keeps its catalog near 3,000 tokens and `make validate` fails above
3,800. If you install other skill packs alongside it and Codex warns
`Exceeded skills context budget`, raise the budget in `~/.codex/config.toml`:

```toml
[skills]
max_context_tokens = 8000   # capped at 10000
```

## Cursor, opencode and GitHub Copilot

All three read Agent Skills from `.agents/skills/` in the project and
`~/.agents/skills/` for the user, so Keystone's skills work unchanged.
`scripts/install_agents.py` links them there and adds what each tool supports:

| | Cursor | opencode | GitHub Copilot |
|---|---|---|---|
| Skills | `.agents/skills/` | `.agents/skills/` | `.agents/skills/` |
| Commands | none needed — skills are invoked with `/` | `.opencode/commands/keystone-*.md` | `.github/prompts/keystone-*.prompt.md` (VS Code, project only) |
| Subagents | not generated yet | `.opencode/agents/*.md` (`mode: subagent`) | `.github/agents/*.md` (project only) |
| Operating contract | `AGENTS.md` | `AGENTS.md`, else `CLAUDE.md` | `AGENTS.md` |
| Runtime hooks | not yet | not yet | not yet |

```bash
python3 ~/dev/keystone/scripts/install_agents.py opencode            # this project
python3 ~/dev/keystone/scripts/install_agents.py opencode --scope user
python3 ~/dev/keystone/scripts/install_agents.py copilot --contract  # adds AGENTS.md if absent
python3 ~/dev/keystone/scripts/install_agents.py cursor --uninstall
```

Skills are symlinked, so `git pull` in Keystone updates them; `--copy` copies
instead (always on Windows). Every generated command, agent and copied skill
records a hash of what was written. A reinstall replaces it, and `--uninstall`
removes it, only while it still matches. Files you wrote are reported as
"kept yours", files of ours you have edited as "edited since install", and
neither is touched. A link to a missing or different Keystone checkout (after
moving your clone, or from a fork) is reported too; delete it and reinstall.

A project install points at your Keystone checkout by absolute path (the skill
links, and the script paths inside generated commands). Keep it out of version
control:

```gitignore
.agents/skills/
.opencode/commands/keystone-*
.opencode/agents/
.github/prompts/keystone-*
.github/agents/
```

Leave out the last two lines if your team keeps its own Copilot agents there.

Live checks after installing:

| Tool | Check |
|---|---|
| Cursor | Customize lists the Keystone skills; typing `/git-workflow` in Agent chat offers the skill |
| opencode | `/` shows the `keystone-*` commands; asking for a review offers the `code-reviewer` subagent |
| Copilot (VS Code) | Typing `/` in chat lists the skills and the `keystone-*` prompts |

These locations were checked against each tool's documentation on 2026-10-22.
Cursor's command and subagent folders and Copilot's hook format were not
verified for this release, so the installer does not write them.

## The operating contract in your own projects

Plugins carry skills; they do not change how an agent reads *your* repository.
For the invariants to apply in a project, the project needs its own contract:

| Agent | Reads | Do this |
|---|---|---|
| Claude Code | `CLAUDE.md`; reads `AGENTS.md` instead only when the project has no `CLAUDE.md` (Claude Code 2.1.277 or later) | `/keystone:onboard` writes it, referencing Keystone's contract |
| Codex | `AGENTS.md`, one per directory from the project root down to the working directory, 32 KiB combined by default | Same content; keep both if the team uses both agents |
| Gemini CLI | The extension's `AGENTS.md` automatically. In your project: `GEMINI.md`, unless `context.fileName` in `.gemini/settings.json` lists `AGENTS.md` | Nothing extra for Keystone's rules. To share your project's own `AGENTS.md`, list it in `context.fileName` instead of writing a `GEMINI.md` copy |

A project used with several agents keeps `CLAUDE.md` and `AGENTS.md` identical —
the same rule Keystone enforces on itself.

```json
{ "context": { "fileName": ["AGENTS.md", "GEMINI.md"] } }
```

That is the whole Gemini setup for a project that already has `AGENTS.md`.

### Why Keystone ships no `GEMINI.md` or `ChatGPT.md`

No agent reads a file named `ChatGPT.md`: Codex — OpenAI's coding agent, also
available from ChatGPT — reads `AGENTS.md`. Gemini CLI loads the extension's
`AGENTS.md` because `gemini-extension.json` names it in `contextFileName`; a
`GEMINI.md` beside it is not the file the manifest names, and a second copy of
the contract would only drift. One contract, two filenames (`CLAUDE.md`, `AGENTS.md`),
checked byte-identical by `make validate`.

Confirm what each agent actually loaded: `/context` in Claude Code, `/status`
in Codex, `/memory show` in Gemini CLI. Checked against each agent's
documentation on 2026-10-23.

## Secrets and agents

All three agents can read files in your project. Before using any of them in a
repository with real credentials, apply `templates/agent-secret-guards.md` and
run `python3 ~/dev/keystone/scripts/check_env.py`. Audit the agents' own
configuration — permissions, MCP servers, hooks — with
`python3 ~/dev/keystone/scripts/audit_agent_config.py` (see
`skills/agent-and-toolchain-security`). Prefer each CLI's login flow
over API keys in files; see `skills/configuration-and-secrets`.

## Keeping adapters in sync

| You changed | Run |
|---|---|
| A skill | nothing — every agent reads `SKILL.md` directly |
| A command in `commands/*.md` | `make adapters` (regenerates `commands/keystone/*.toml`) |
| A version | the same number in all four manifests; `make validate` checks |

Never edit `commands/keystone/*.toml` by hand. CI and pre-commit fail on a stale
or hand-edited adapter.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Claude `/plugin` shows `Invalid input` | manifest field shape | `claude plugin validate ~/dev/keystone`; `make validate` mirrors its rules |
| Gemini: commands missing | extension disabled or not linked | `gemini extensions list`; `gemini extensions enable keystone` |
| Gemini: skills never activate | `skills.enabled` false | re-enable in `settings.json`, restart |
| Codex: plugin not listed | marketplace not added | `codex plugin marketplace list` |
| Codex: skills ignored | catalog over budget | see the budget section |
| Any agent: wrong skill fires | description overlap | fix the description, add the prompt to `evals/cases`, `make triggers` |
| Hooks never fire | profile `off`, hook disabled, or (Codex) not trusted | `KEYSTONE_HOOK_DEBUG=1`; `/hooks`; see `docs/hooks.md` |
| Cursor/opencode/Copilot: skills missing | not installed in this project | `install_agents.py <tool>`; check `.agents/skills/` |

These manifests were checked against the agents' own loaders (Gemini CLI and
Codex source as of 2026-09-30) rather than only their documentation. Agent CLIs
change quickly — if a loader starts rejecting a manifest, `make validate` is the
place to encode the new rule.
