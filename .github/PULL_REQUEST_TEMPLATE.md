## What and why

<!-- What changed, and the reason it needed to change. Not a restatement of the diff. -->

## Verification

<!-- What you ran and what you observed. "Tests pass" is not verification — say which. -->

- [ ] `make all` green
- [ ] Tests added or updated, and observed failing before the fix
- [ ] Full suite run, not only the focused test

## Reviewer attention

<!-- Where should the reviewer look hardest? What are you least sure about? -->

## Risk and rollback

- Blast radius:
- Rollback path:
- Irreversible steps (migration, deletion, external write):

## Bar protection

- [ ] No new suppression without a justification and a link
- [ ] No test deleted, skipped, or assertion weakened
- [ ] No `CONSTRAINTS.md` threshold lowered in this PR
- [ ] No fixture or golden file changed together with the logic that produces it

<!-- If any box above is unchecked, say why here. -->
