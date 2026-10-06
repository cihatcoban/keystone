# Agent secret guards

Snippets that stop AI coding agents from reading `.env` and other secret files.
Apply the ones for every agent your team uses. See
`skills/configuration-and-secrets` for why, and for the limits of each.

## Claude Code — `.claude/settings.json` (committed, applies to everyone)

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)"
    ]
  }
}
```

`.env.example` is matched by `./.env.*` too. If the agent needs to see the
variable *names*, keep them in a differently named file the rule does not match
(for example `config/env.reference`), or accept that the agent asks you.

Run `/status` in a session to confirm the settings file loaded.

## Gemini CLI — `.geminiignore` (gitignore syntax)

```gitignore
.env
.env.*
!.env.example
secrets/
```

Gemini CLI's file tools refuse paths matched by its ignore patterns. `.gitignore`
entries are also respected when Git-ignore filtering is enabled in settings.

## Codex — filesystem read-deny

Codex enforces `permissions.filesystem.deny_read` patterns from its requirements
configuration (glob patterns are accepted). Where your installation reads that
file depends on how Codex is deployed (user, admin or managed policy); check the
current Codex documentation for the location before relying on it.

```toml
[permissions.filesystem]
deny_read = ["**/.env", "**/.env.*"]
```

## What none of these cover

- **Shell access.** Read-deny rules govern file tools. `cat .env`, `env` or
  `printenv` go through the shell permission instead. Keep shell commands gated
  (ask, allow-list or sandbox) in any repository holding real secrets.
- **The agent's own environment.** Variables exported in the shell that started
  the agent are visible to every command it runs. Do not start agent sessions
  from a shell that has production credentials loaded.
- **Pasting.** A key pasted into the chat is a leaked key. Rotate it.
