---
description: Review changes before merge across all axes, with a verdict
---

Apply `code-review-and-quality`.

Input: $ARGUMENTS (defaults to staged changes or the current branch diff)

1. Bar-protection scan first (`CLAUDE.md` §4) — report hits before anything else.
2. Scope check: does the diff match its description and nothing more?
3. Axes: correctness · failure behavior · design · security · performance · tests.
4. Review the tests for whether they could actually fail.
5. Findings as `[BLOCKER|IMPORTANT|SUGGESTION] file:line` with impact and fix.
6. End with exactly one verdict: APPROVE / APPROVE AFTER FIXES / REQUEST CHANGES.
