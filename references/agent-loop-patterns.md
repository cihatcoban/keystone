# Agent Loop Patterns

Detail for `agent-orchestration`. Pick the shape from the skill's table, then
use the section here. Every shape inherits the skill's loop spec and stop
conditions; a section below only adds what is specific to it.

## Fix-until-green

```text
loop:
  run the check → pass? write state, stop (done)
  same failure signature as an earlier iteration? → stop, escalate
  diagnose (debugging-and-root-cause) → smallest fix → bar-protection scan
  write state
```

- The **failure signature** is the failing check plus the first error line,
  normalised (paths, line numbers, timestamps stripped). Compare it with every
  earlier iteration, not only the last.
- A fix that touches the check, its config or its fixtures is not a fix; the
  bar-protection scan stops it.

## Plan–execute–verify

```text
for step in plan (in order):
  execute step
  verify step with its own evidence command
  failed twice? → stop: report done steps, the failing step, the rest untouched
  write state: step id, evidence, commit
```

- Each plan step names its evidence before execution starts (see
  `test-driven-development`, evidence map).
- Never reorder the plan mid-run to get past a failing step; a step that must
  move means the plan is wrong — stop and say so.

## Generator–evaluator

```text
rubric = fixed before round 1 (criteria, weights, pass bar)
round 1..max_rounds (3–5):
  generator produces candidate (sees rubric and last critique, not the scores history)
  evaluator scores candidate against rubric, with evidence per criterion
  score ≥ bar → stop (done)
  score not up by ≥ the stated minimum over the last 2 rounds → stop (plateau)
```

- Generator and evaluator are **separate contexts**. The evaluator never sees
  the generator's reasoning; the generator never edits the rubric.
- Every score cites evidence ("criterion 3: 2/5 — no error contract for the
  timeout case, §4"). A score without evidence is discarded.
- Keep the best-scoring candidate; the last one is not necessarily the best.
- Watch for rubric gaming: a jump in score with no visible change in substance
  is a finding, not a success.

## Fan-out / fan-in

- Contracts first, one owner per path, self-contained briefs (skill body).
- The parent sets a deadline per part. A part that misses it is reported as
  missing; the merge does not wait forever.
- Fan-in = read every return, list contradictions, merge, run `/verify` on the
  whole. Parts that passed alone are not evidence for the whole.

## Panel

- One artifact, N lenses, each in a fresh context with the same inputs (spec,
  diff, bar) and a different brief: `security-auditor`, `performance-auditor`,
  `test-engineer`, `silent-failure-hunter`, `adversarial-reviewer`.
- Each lens returns findings in the `code-review-and-quality` format, or
  "nothing found" plus what it checked.
- The parent de-duplicates and keeps the highest severity per finding.
  Conflicting recommendations go to a person with both arguments; counting
  votes hides the reason one lens disagreed.

## Unattended and scheduled

Everything above, plus:

- **Preflight**: confirm the done signal, the budget and the kill switch exist
  before the first iteration; refuse to start without them.
- **Kill switch**: a file or flag checked at the top of every iteration
  (for example `.keystone/state/<loop>.stop`). Present → finish the current
  write, record "stopped by operator", exit.
- **Irreversible steps**: the run prepares the step, records it as pending, and
  stops. A person approves; the next run executes it.
- **Report on every exit** — done, budget, plateau, oscillation, stopped:
  what changed, what was verified, what is pending. An unattended run with no
  report is indistinguishable from one that did damage.

## State file

Written after every iteration, read first on every start. Plain text or JSON,
inside the repository's ignored state directory, never in the conversation.

```json
{
  "loop": "nightly-lint-fix",
  "spec": { "goal": "...", "done": "make lint", "budget": { "iterations": 8, "minutes": 45, "tokens": 400000 } },
  "iteration": 3,
  "status": "running | done | stopped | escalated",
  "progress": [ { "iteration": 1, "metric": 14 }, { "iteration": 2, "metric": 9 } ],
  "signatures_seen": ["lint:E501 src/a.py", "lint:F401 src/b.py"],
  "pending_irreversible": [],
  "last_commit": "abc1234"
}
```

Resume rule: if the state says `done` or `escalated`, do not start again
without a person; if `running`, continue from `iteration + 1`, re-running the
done signal first — the world may have changed since the last write.

`templates/handoff.template.md` is the human-readable counterpart for a
session that ends mid-loop.

## Reviewing an existing loop

Answer each with evidence from the loop's code or config:

1. Can the worker reach the done signal by editing it? (yes → mis-specified)
2. Is there a ceiling on iterations **and** time **and** tokens?
3. Does a restart resume from state, or redo work?
4. What does the loop do at an irreversible step?
5. What does a person see when it stops — and when it never starts?

Any "no answer" is the first fix.
