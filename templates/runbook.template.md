# Runbook: <exact alert or scenario name>

> Written for someone who did not build this system and was just woken up.
> Exact commands, not "check the logs".

## What this means
One or two sentences in plain language.

## User impact
Who is affected and how they experience it. If none, say so — that changes the
urgency.

## Severity guidance
When this is a page vs a ticket.

## First checks
1. `<exact command>` — expected: `<what healthy looks like>`
2. `<exact command>` — expected: …
3. Dashboard: `<link>` — look at `<panel>`

## Mitigations, in order of preference
1. **Flag off:** `<command or link>` — effect, and how to verify
2. **Roll back:** `<command>` — how long it takes
3. **Scale / restart:** `<command>` — when this is appropriate
4. **Degrade:** `<what to disable>` — what users lose

## Do not
Actions that make it worse (e.g. restarting before capturing a heap dump,
clearing the queue, editing data directly).

## Escalation
Who, how to reach them, and at what point.

## Related
Dashboard · ADR · recent incidents · the service's README

## Last exercised
YYYY-MM-DD by <name>. A runbook nobody has followed is fiction.
