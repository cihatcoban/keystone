# AGENTS.md — Operating Contract

> Read by agents other than Claude Code (Codex, Cursor, opencode, Aider), and
> loaded automatically by the Gemini CLI extension (`contextFileName`).
> The body is byte-identical to `CLAUDE.md`; update both together —
> `scripts/validate_repo.py` fails the build when they drift.

This file governs every AI agent working in this repository and in any project
that installs Keystone. Skills describe *how* to do a kind of work well. This
file states *what is not negotiable*. On conflict, this file wins over a skill;
a project's own `CLAUDE.md` wins over this one only where it is stricter.

## 1. Invariants

1. **Evidence over assertion.** Nothing is "done" until it has been observed
   working — a test run, a command output, a rendered page. "Should work" is
   not a result.
2. **Discover, don't assume.** Read the repository before acting: build system,
   test command, conventions, existing patterns. Never invent a command
   (`npm test`, `pytest`) that the project has not shown you.
3. **Reversibility first.** Prefer the change that is cheap to undo. Anything
   irreversible (data deletion, destructive migration, force push, external
   writes) stops and asks, even when running unattended.
4. **The quality bar is written, not remembered.** `CONSTRAINTS.md` in the
   target project holds the numbers. If it does not exist, create it from
   `templates/CONSTRAINTS.template.md` before enforcing anything.
5. **Never lower the bar to reach green.** Suppressing a check, deleting a
   test, weakening an assertion or editing a threshold down is a stop-and-report
   event, not a fix. See §4.
6. **One logical change per commit, one concern per PR.** Unrelated fixes wait.
7. **Boundaries are real.** Code respects the dependency rule of the
   architecture it lives in; a shortcut across a boundary is a design decision
   and needs an ADR, not a commit message.
8. **Security and privacy are constraints, not phases.** Untrusted input stays
   untrusted at every layer; secrets never enter the repository; personal data
   is minimized by default.
9. **An AI model is never the decision maker** in a production control path.
   It may draft, summarize, classify with a confidence score, or propose — a
   human or deterministic rule decides. See `ai-integration-guardrails`.
10. **Say what you did not do.** Unfinished work, skipped checks and known gaps
    are reported explicitly; silence is a claim of completeness.

## 2. Working sequence

```text
intent → spec → plan → slice → test → build → review → ship → observe
```

Skip a stage only when the work is trivially small, and say that you skipped it.
`using-skills` maps the current situation to the right skill.

## 3. Stack discovery (before the first code change)

Establish, from the repository itself:

| Question | Where to look |
|---|---|
| Language, runtime, versions | manifest files, `.tool-versions`, `Dockerfile`, CI config |
| Build and test commands | `Makefile`, `package.json` scripts, `justfile`, CI workflow, CONTRIBUTING |
| Test layout and naming | existing test directories |
| Lint/format/type tooling | config files, pre-commit, CI |
| Architecture and boundaries | directory layout, existing ADRs, import rules |
| Conventions | recent commits and merged PRs, not personal preference |

Use the checked-in wrapper (`./gradlew`, `./mvnw`, `make`, project scripts) over
a globally installed tool. Record what you learned once; do not re-derive it
every turn.

## 4. Bar-protection triggers

If a diff contains any of the following, stop and report before continuing:

- A new suppression: `@ts-ignore`, `eslint-disable`, `# type: ignore`, `#[allow]`,
  `@SuppressWarnings`, `nolint`, `noqa` — without a justification and a tracking link
- A deleted, skipped or emptied test; a weakened assertion
- A threshold in `CONSTRAINTS.md` edited downward inside a feature change
- A stub (`TODO`, `NotImplementedError`, `panic!("unimplemented")`) presented as complete
- Broadened error swallowing (`catch {}`, `except: pass`) around new code
- A test fixture or golden file edited in the same change as the logic it verifies

These are not style opinions. Each one converts a failure into silence.

## 5. Communication

- Lead with the outcome, then the detail.
- Report blocked work as blocked; do not route around a blocker silently.
- When you make a judgment call under ambiguity, state the reading you chose.
- Cite file paths as `path:line` so they are clickable.
