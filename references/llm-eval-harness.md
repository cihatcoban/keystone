# LLM eval harness

How to build the eval set that `ai-integration-guardrails` requires before an
LLM feature ships: the shape of the data, the graders, the metric, and the gate
that blocks regressions. Stack-agnostic; the runner is a test like any other.

## The dataset

One case per line in a versioned file (JSONL works everywhere; wrapped here
for width):

```json
{"id": "refund-007", "input": {"ticket": "..."}, "expected": {"intent": "refund", "amount": 42.0},
 "tags": ["refund", "currency", "hard"], "source": "prod-2026-09, anonymized"}
```

| Rule | Why |
|---|---|
| 50–200 cases to start, drawn from real inputs | Synthetic cases test what you imagined, not what users send |
| Tag every case (intent, language, length, known-hard, adversarial) | Aggregate scores hide the slice that regressed |
| Include an injection and abuse slice | Inputs that try to override instructions, exfiltrate the prompt or trigger tools |
| Anonymize before it enters the repository | Eval data is still personal data (`references/privacy-compliance.md`) |
| Never tune the prompt on the held-out slice | Otherwise the eval measures memorization |
| Add every production correction as a case | The set grows where the model actually fails |

## Graders, cheapest first

| Grader | Use for | Watch out for |
|---|---|---|
| Schema validation | Every structured output | Necessary, never sufficient |
| Exact / normalized match | Labels, ids, numbers | Normalize case, whitespace, number format first |
| Rule checks | Must-include / must-not-include facts, citation present, no PII | Brittle wording rules; check meaning-bearing tokens |
| Reference similarity | Summaries against a gold answer | Rewards paraphrase of the gold, not correctness |
| Model-as-judge with a rubric | Open-ended quality | Calibrate against ≥ 50 human-labeled cases; report agreement; pin the judge model and prompt |

A model judging its own family's output inflates scores; prefer a different
model or human spot checks on a sample.

## Retrieval is evaluated on its own

When answers come from retrieved context, a wrong answer has two possible
causes, and one end-to-end score cannot tell them apart. Label, per case, which
source passages answer it, then measure both stages:

| Stage | Metric | Question it answers |
|---|---|---|
| Retrieval | Context recall | Did the passages needed for the answer reach the model? |
| Retrieval | Context precision | How much of what reached the model was relevant? |
| Generation | Faithfulness | Is every claim in the answer supported by the passages given? |
| Generation | Citation validity | Does every cited source exist in the passages, and say what is claimed? |
| Generation | Abstention | On cases the corpus cannot answer, did it say so instead of answering? |

Include unanswerable cases on purpose — a pipeline that never abstains scores
well until a user asks about something the corpus does not contain. Gate
retrieval changes (chunking, embedding model, reranker, top-k) on the
retrieval metrics, not only on the final answer.

## The metric matches the cost

Write down what a wrong answer costs versus an abstention before choosing the
metric. Typical choices: precision at the auto-accept threshold, recall on the
must-not-miss slice, the rate of confident wrong answers, and cost and latency
per case. Report every metric per tag slice, not only overall.

## The regression gate

- Store a baseline result file next to the dataset.
- Run the eval in CI on every change to prompts, model version, retrieval,
  tools or the dataset itself.
- Fail on a drop beyond a stated tolerance in any gated metric or slice, and on
  any new failure in the injection slice.
- Non-determinism: fix temperature where possible; otherwise run each case n
  times and gate on the rate, with n and the tolerance written in
  `CONSTRAINTS.md`.
- Record model id, prompt version, dataset version and cost with every run, so
  a regression can be traced to what changed.

## In production

Log inputs, outputs and versions (minus personal data), sample them for human
review, and track the acceptance rate of drafts. A falling acceptance rate is
the earliest drift signal; turn the rejected cases into new eval cases.

## Anti-patterns

- **Vibe checks.** Five hand-picked prompts in a notebook are a demo, not an eval.
- **Moving the goalposts.** Editing expected outputs to match a new model's
  answers without review is lowering the bar (`CLAUDE.md` §4).
- **One number.** An overall score that rose while the refund slice fell is a
  regression.
