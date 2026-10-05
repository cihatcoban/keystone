---
description: Find the root cause systematically instead of guessing
---

Apply `debugging-and-root-cause`.

Input: $ARGUMENTS (symptom, error, or failing test)

1. Capture evidence and save the triggering input as a fixture.
2. Get to a single-command reproduction.
3. Narrow by bisection — time, input, layer. State a falsifiable hypothesis
   before each experiment.
4. Explain every symptom before declaring a cause.
5. Write the reproduction test, see it fail, then fix.
6. Search for siblings of the same mistake and report what would have caught it.
