# Multi-agent setup — Claude Code, Gemini CLI, Codex

Keystone is one source of truth packaged three ways. The skills, the operating
contract and the subagents are shared; each agent gets the manifest its loader
expects. Nothing is maintained twice by hand.

## What each agent gets

| | Claude Code | Gemini CLI | Codex (ChatGPT) |
|---|---|---|---|
| Manifest | `.claude-plugin/plugin.json` | `gemini-extension.json` | `plugin.json` (Agent Plugins schema) |
| 32 skills (`skills/*/SKILL.md`) | native | native | native |
| Operating contract | via the project's `CLAUDE.md` | **loaded automatically** (`contextFileName: AGENTS.md`) | via the project's `AGENTS.md` |
| 16 commands | `/keystone:<name>` from `commands/*.md` | `/keystone:<name>` from generated `commands/keystone/*.toml` | no plugin commands — invoke the skill: `$code-review-and-quality` |
| 6 subagents (`agents/*.md`) | native | native | not supported by Codex plugins |
| Local install | `--plugin-dir` | `gemini extensions link` | `.agents/plugins/marketplace.json` |

Every manifest carries the same version. `make validate` fails if they diverge,
if a manifest has a shape its agent rejects, or if a generated Gemini command
is out of date.

## Claude Code

```bash
claude plugin validate ~/dev/keystone        # must pass
claude --plugin-dir ~/dev/keystone           # this session only
```

Check: `/plugin` → **Errors (0)**; type `/keystone:` and the 16 commands appear.

## Gemini CLI

```bash
npm install -g @google/gemini-cli            # or: brew install gemini-cli
gemini extensions link ~/dev/keystone        # symlink: edits are live
gemini extensions list                       # keystone should be listed
```

Inside a session:

- `/keystone:review`, `/keystone:spec` … — same names as in Claude Code.
  Gemini renames an extension command only if it collides with another one.
- `/skills` lists the 32 skills; Gemini activates them on demand and asks
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

Keystone keeps its catalog near 2,800 tokens and `make validate` fails above
3,800. If you install other skill packs alongside it and Codex warns
`Exceeded skills context budget`, raise the budget in `~/.codex/config.toml`:

```toml
[skills]
max_context_tokens = 8000   # capped at 10000
```

## The operating contract in your own projects

Plugins carry skills; they do not change how an agent reads *your* repository.
For the invariants to apply in a project, the project needs its own contract:

| Agent | Reads | Do this |
|---|---|---|
| Claude Code | `CLAUDE.md` | `/keystone:onboard` writes it, referencing Keystone's contract |
| Codex | `AGENTS.md` | Same content; keep both if the team uses both agents |
| Gemini CLI | the extension's `AGENTS.md` automatically; your project's `GEMINI.md` | Nothing extra needed for Keystone's rules |

A project used with several agents keeps `CLAUDE.md` and `AGENTS.md` identical —
the same rule Keystone enforces on itself.

## Secrets and agents

All three agents can read files in your project. Before using any of them in a
repository with real credentials, apply `templates/agent-secret-guards.md` and
run `python3 ~/dev/keystone/scripts/check_env.py`. Prefer each CLI's login flow
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

These manifests were checked against the agents' own loaders (Gemini CLI and
Codex source as of 2026-09-30) rather than only their documentation. Agent CLIs
change quickly — if a loader starts rejecting a manifest, `make validate` is the
place to encode the new rule.
