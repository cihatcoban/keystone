---
name: planning-and-task-breakdown
description: Decomposes an approved spec into small, ordered, independently verifiable tasks. Use when a spec exists and the work must be sequenced, or when a task feels too large to start. Triggers - break this down, make a plan, task list, where do we start, sequence the work, this task is too big, estimate scope.
---

# Planning and Task Breakdown

Decomposition decides whether work lands smoothly or becomes a three-week
branch nobody can review. The goal is a sequence of slices, each of which
leaves the system **working, tested and shippable** — even if the feature is
not yet visible.

## The task test

A task is correctly sized when all of these hold:

- It maps to one acceptance criterion (or one clear part of one)
- It ships with its own test
- It is one reviewable commit or a small PR (≤ ~400 changed lines)
- The system is releasable when it lands — behind a flag if incomplete
- "Is it done?" has an unarguable answer
- One focused session finishes it

Any failure means split. A task that cannot be split without leaving the system
broken usually indicates a design problem, not a planning problem — say so.

## Vertical, not horizontal

The most common decomposition error is slicing by layer.

| Horizontal (wrong) | Vertical (right) |
|---|---|
| "Build all the data models" | "One entity end to end: schema → API → UI → test" |
| "Write the API layer" | "One endpoint, real response, contract test" |
| "Add all validation" | "Reject the one invalid case that matters most, with a test" |

Horizontal slices integrate at the end, which is where the surprises are.
Vertical slices surface them on day one.

## Ordering

1. **Unknowns first.** The task whose outcome could change the plan goes first,
   even if it is not the foundation. A spike is a legitimate first task, with a
   time box and a question it must answer.
2. **Contracts before consumers.** The interface (schema, API shape, event
   format) is agreed before both sides build against it.
3. **Reversible before irreversible.** Postpone data deletion, public API
   commitments and vendor lock-in until you have learned what you can.
4. **Walking skeleton early.** One thin path through every layer, end to end,
   before depth anywhere. It proves the integration, deployment and observability
   all exist.
5. **Cleanup is a task, not a hope.** Flag removal, dual-write teardown and
   dead-code deletion get their own numbered entries.

## Plan shape

`docs/plans/NNN-short-name.md`

```markdown
# Plan: <spec title>
Spec: docs/specs/NNN-....md

## Tasks
- [ ] T1 — <imperative verb + object>
      Criterion: <observable, from the spec>
      Test: <what proves it>
      Size: S | M | L
      Depends on: —
- [ ] T2 — ...

## Sequencing rationale
Why this order. Which task resolves the most uncertainty.

## Risk
The task most likely to invalidate the plan, and what we do if it does.

## Rollout
Flag name, who sees it first, what makes it default, when the flag is removed.
```

## Sizing

Use S / M / L, not hours.

- **S** — path is obvious, no unknowns
- **M** — one unknown, resolvable within the task
- **L** — two or more unknowns → **split it now**; L never survives into a plan

Sizing is an uncertainty signal, not a schedule. If someone needs dates, count
S/M items and state the assumption explicitly.

## Replanning

Plans are wrong on contact; that is expected, not a failure. Replan when:

- A task turns out 3× its estimate → the decomposition was wrong, redo it
- A spike invalidates an assumption → revisit the spec, not just the plan
- Two tasks keep blocking each other → the boundary between them is wrong
  (`boundaries-and-dependencies`)

Update the plan file. A plan that has silently diverged from reality is worse
than none, because people still trust it.

## Exit checklist

- [ ] Every task maps to a spec criterion
- [ ] Every task is vertical and independently verifiable
- [ ] No L-sized tasks remain
- [ ] Highest-uncertainty task is first or near-first
- [ ] Dependencies are explicit; no hidden ordering
- [ ] Cleanup and flag-removal tasks exist
- [ ] Rollout plan names the flag and its removal condition
