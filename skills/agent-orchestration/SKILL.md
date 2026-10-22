---
name: agent-orchestration
description: Coordinates several agents on one task - splitting work, running subagents in parallel, fresh-context verification, stop conditions for loops and budgets. Triggers - use subagents, run this in parallel, split this across agents, agent keeps retrying, verify with a fresh agent, orchestrate.
---

# Agent Orchestration

One agent with a long context is the default, and usually the right one. More
agents pay off in three situations: work that splits into **independent** parts,
a **broad search** whose details nobody needs to keep, and **verification by an
agent that has not seen the work**. Everywhere else, coordination costs more
than it saves — every subagent starts cold and re-derives context the parent
already had.

## When to split

| Situation | Split? | Shape |
|---|---|---|
| Independent changes in separate areas (three services, five docs) | Yes | One agent per area, in parallel |
| A wide search: "where is X used", "which modules do Y" | Yes | A subagent returns the conclusion, not its reads |
| Review, adversarial check, security audit of finished work | Yes | A fresh agent with the diff and the spec only |
| One feature across tightly coupled files | No | One agent, sequential slices (`incremental-delivery`) |
| Debugging an unexplained failure | No | One agent holding the whole picture (`debugging-and-root-cause`) |
| The task is small | No | Coordination overhead exceeds the work |

The test: could two agents work on this without reading each other's output?
If not, they are one task.

## Splitting work

1. **Contracts first.** If parts meet at an interface, fix the interface (types,
   schema, API) before fanning out (`api-and-contract-design`). Parallel agents
   negotiating an interface through code produce two interfaces.
2. **One owner per file.** Assign files or directories, never overlap. Two
   agents editing one file is a merge conflict scheduled in advance.
3. **Self-contained briefs.** Each brief carries the goal, the files it owns,
   the contract it must honor, the constraints (`CONSTRAINTS.md`), and what to
   return. A subagent cannot ask the parent's context what was meant.
4. **A defined return shape.** Ask for a summary, the files changed, the
   commands run with their result, and open questions — not a narrative.

## Verification by fresh context

An agent grading its own work finds what it expected to find. Keystone's
reviewers exist for this:

| Check | Agent |
|---|---|
| Is this plan or conclusion wrong? | `adversarial-reviewer` |
| Is this change ready to merge? | `code-reviewer` |
| Does it hide failures? | `silent-failure-hunter` |
| Is it secure? | `security-auditor` |
| Are the tests meaningful? | `test-engineer` |

Give the reviewer the spec, the diff and the bar — not the author's reasoning,
which would anchor it. The parent acts on findings; the reviewer does not fix.

## Stop conditions

Loops are the expensive failure: an agent retrying the same fix, or two agents
handing a task back and forth. Set the limits before starting:

- **Same failure twice → change approach.** A third identical attempt is not
  persistence; escalate with what was tried.
- **No measurable progress in N iterations → stop.** Progress means a check
  turned green, a test count rose, a finding closed — not more text.
- **Budget.** A ceiling on iterations, wall time or tokens per agent; exceeding
  it ends the run with a report, never a silent continuation.
- **Disagreement between agents → a human.** Do not let a third agent break the
  tie by majority.

`build-error-resolver` follows these limits for build failures: it fixes, it
reruns, and after its attempts it reports what remains instead of disabling a
check.

## Merging results

The parent integrates, and owns the outcome:

1. Read every return; contradictions between them are findings, not noise.
2. Run the full verification (`/verify`) on the combined result — parts that
   each passed can still fail together.
3. Report which agent did what, what was verified, and what was not.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Two agents changed the same file | Ownership not assigned | Partition by path before starting |
| Subagent solved a different problem | Brief relied on the parent's context | Self-contained brief with goal and constraints |
| Results look fine, combined build fails | Integration never verified | `/verify` after merging, every time |
| Cost far above estimate | Agents re-reading the same files, retry loops | Shared conclusions in files; stop conditions |
| Reviewer approves everything | It saw the author's reasoning | Give it only spec, diff and bar |

## Exit checklist

- [ ] Split only for independent parts, broad searches, or fresh-context review
- [ ] Interfaces fixed before fan-out; each file has exactly one owner
- [ ] Every brief self-contained, with a defined return shape
- [ ] Stop conditions and budget set before starting
- [ ] Work verified by an agent that did not produce it
- [ ] Combined result passed `/verify`; who did what is reported
