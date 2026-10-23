# Privacy

Keystone collects no data. It has no servers, no accounts, no analytics and no
telemetry, and its maintainer receives nothing from your use of it.

## What stays on your machine

- **Skills, commands and subagents** are Markdown files your agent reads. They
  send nothing anywhere.
- **Runtime hooks** read your project's files and run read-only `git`
  commands. They write only under your project's `.keystone/state/` folder,
  which is git-ignored and which you can delete at any time. They make no
  network calls.
- **Scripts in `scripts/`** run only when you run them, on your machine.
  `evals_live.py` drives an agent CLI you choose, which sends prompts to that
  agent's model provider under your own account and that provider's terms.

## What leaves your machine

Nothing that Keystone sends. Your coding agent itself — Claude Code, Gemini
CLI, Codex or another — sends your conversation, including any skill it loads,
to its model provider under that provider's privacy policy.

## Contact

Questions or concerns: open an issue at
<https://github.com/cihatcoban/keystone/issues>. Report security issues
privately as described in [SECURITY.md](SECURITY.md).
