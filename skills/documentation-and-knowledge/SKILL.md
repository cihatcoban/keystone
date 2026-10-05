---
name: documentation-and-knowledge
description: Writes documentation that stays true and gets used - READMEs, runbooks, ADRs, API docs - and prunes what has rotted. Use when shipping something others will operate or integrate with, or when the docs are misleading. Triggers - write documentation, README, runbook, document this, the docs are wrong, onboarding guide, how does this work, API docs, knowledge transfer.
---

# Documentation and Knowledge

Wrong documentation is worse than none: it is trusted, and it misleads at the
moment of maximum pressure. So the governing rule is not "document more" — it
is **write the few documents people actually use, and keep them true.**

## What is worth writing

| Document | Reader | Answers | Rots |
|---|---|---|---|
| README | Someone arriving | What is this, how do I run it, where do I go next | Fast |
| Runbook | On-call at 3am | This alert fired — what do I do | Fast |
| ADR | Future engineer | Why is it like this | Never (immutable) |
| API reference | Integrator | What can I call, what comes back, what errors | Generate it |
| Architecture overview | New team member | How do the pieces fit | Slowly |
| Postmortem | The organization | What happened and what we changed | Never |

Anything not on this list needs a reason. Tutorials for an internal tool with
four users, exhaustive prose about code that changes weekly, and diagrams of
last year's design are net-negative.

## The rot rule

Documentation degrades in proportion to the distance from the thing it
describes.

1. **Generate what can be generated** — API reference from the schema, CLI help
   from the parser, config reference from the definitions. A hand-written API
   doc is wrong within a month.
2. **Point, don't duplicate.** Link to the code or the schema instead of
   restating it. Every restatement is a future inconsistency.
3. **Document decisions, not mechanics.** Mechanics are visible in code and
   change constantly; the *reason* is invisible and stable — and it is exactly
   what the reader cannot reconstruct.
4. **Put it in the repository.** Docs in a separate wiki drift immediately
   because they are not in the diff.
5. **Prune on contact.** If you find a stale line while reading, fix it in that
   session. Stale docs compound because readers stop trusting all of them.

## README

The only document everyone reads. Keep it under a screen and a half:

```markdown
# Name
One sentence: what it does and for whom.

## Run it
Prerequisites, then the exact commands, copy-pasteable. Verified today.

## Test it
Fast tier and full suite commands.

## How it fits
Three sentences plus a link to the architecture doc if one exists.

## Where things are
The three or four directories that matter, one line each.

## Gotchas
Things that look wrong and are deliberate.

## Links
Runbook · ADRs · dashboards · the team channel
```

Every command in it must have been run successfully by the author, today. A
broken setup command is the most expensive documentation bug there is —
it costs every newcomer their first hour and their confidence.

## Runbook

Written for someone who did not build the system and is not fully awake.

```markdown
# Alert: <exact alert name>
## What it means
## User impact
## First checks (exact commands, expected output)
1. ...
## Mitigations, in order of preference
## Escalation: who, how, when
## Related: dashboard, ADR, recent incidents
```

Exact commands, not "check the logs". Test it by having someone unfamiliar
follow it during a drill — a runbook that has never been followed is fiction.

## Architecture overview

One page plus a diagram. Use the C4 levels of zoom: **context** (systems and
who uses them), then **containers** (deployable units and how they communicate),
then **components** only where a subsystem is genuinely intricate. Almost
nobody needs class-level diagrams; they are always out of date.

Diagram as code (Mermaid, PlantUML, D2) in the repository, so a diagram change
appears in the diff and can be reviewed.

## For agents specifically

The operating contract (`CLAUDE.md` / `AGENTS.md`) is documentation with an
unusual property: it is read *every* session, so inaccuracy is amplified.
`context-engineering` covers it.

## Exit checklist

- [ ] Every command in the README was executed successfully today
- [ ] Generated docs are generated, not hand-maintained
- [ ] Each alert has a runbook with exact commands
- [ ] Decisions recorded as ADRs, not as prose scattered in the wiki
- [ ] Diagrams are text-based and live in the repository
- [ ] Stale content found while working was removed, not left
- [ ] Nothing duplicates what the code or schema already states
