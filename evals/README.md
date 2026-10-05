# Evals

These cases test **routing** — whether a skill is selected when it should be,
and stays quiet when it should not. Routing happens on the `description` field
alone, so that is what these exercise.

## Case shape

```json
{
  "skill_name": "performance-engineering",
  "trigger": {
    "positive": [{ "prompt": "This endpoint is slow", "top_k": 3 }],
    "negative": [{ "prompt": "Write the ADR" }]
  },
  "expectations": ["..."]
}
```

Minimum: 3 positive, 2 negative. Positives are phrases a person would actually
type under pressure — not the formal name of the discipline. Negatives belong
to a neighbouring skill and are how description collisions get caught.

## Running

**Static (CI, free, no model):**

```bash
python3 scripts/check_triggers.py
```

Flags two failures: a positive prompt sharing no vocabulary with its own
skill's description, and a negative prompt matching this skill at least as well
as the skill that should own it.

**Live (manual, occasional):** in a fresh session, type the positive prompt and
observe which skill fires. Wrong skill → the two descriptions overlap; sharpen
both and state the boundary in each. No skill → vocabulary is missing from the
description.

## When a skill does not trigger

Fix the **description**, never the body. The body is invisible until the skill
is already selected, so lengthening it cannot help. Add the phrase, add it to
the eval case, re-run the static check.
