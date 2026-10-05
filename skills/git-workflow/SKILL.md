---
name: git-workflow
description: Keeps version history reviewable and recoverable - atomic commits, branch strategy, conflict resolution, PR hygiene, bisect and recovery. Use when committing, branching, splitting messy work, opening a PR, or recovering from a bad git state. Triggers - commit this, write a commit message, branch strategy, merge conflict, rebase or merge, split this commit, git bisect, undo a commit, PR description, messy working tree.
---

# Git Workflow

History is documentation that cannot go stale. Its value shows up on the worst
day: when you need to know why a line exists, which change broke production, or
how to undo exactly one thing. Every habit below is in service of those three
moments.

## Commits

A commit is **one logical change**, and the repository works at that commit.

- Separate structural from behavioral changes (`refactoring-and-simplification`).
- Separate mechanical churn (formatting, generated files, dependency bumps)
  from real changes. Otherwise the real change hides inside 4,000 lines.
- Use staged hunks (`git add -p`) to split work that grew tangled. If a commit
  message needs "and", split it.

### Message

```
type(scope): imperative summary, ≤ 72 chars

Why this change exists — the condition or decision that required it, not a
restatement of the diff. The diff already says what changed.

Consequences the reader needs: behavior change, migration required, flag added.

Refs: #123
```

Types: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `build`, `ci`, `chore`.
Mark breaking changes explicitly (`feat(api)!:` plus a `BREAKING CHANGE:` note)
— release tooling and humans both depend on it.

**The message answers "why".** In six months you will have the diff and not the
context; write the sentence you will want then.

## Branching

Prefer **trunk-based**: short-lived branches (hours to two days), merged behind
flags. Long-lived branches are deferred integration, and the interest
compounds — the conflict cost grows with the square of the divergence.

| Model | Use when |
|---|---|
| Trunk-based + flags | Default. Continuous deployment, small team, good tests |
| Short-lived feature branches + PR | Default with review requirements |
| Release branches | You must support multiple released versions |
| Long-lived develop branch | Rarely justified today; it doubles integration points |

## Rebase vs merge

- **Rebase your own unpublished branch** onto the latest trunk before opening a
  PR: linear, reviewable, bisectable history.
- **Never rebase a branch others have based work on.** Rewriting shared history
  forces everyone else to recover.
- **Merge commits for integrating a reviewed PR** are fine; pick one convention
  per repository and enforce it in settings rather than by reminder.
- Never `push --force` to a shared branch. `--force-with-lease` on your own
  branch only.

## Conflicts

A conflict means two intentions met. Resolve by understanding both, not by
picking a side quickly.

1. Read both sides and, if needed, the commits that produced them.
2. Resolve for the *intent*, which is sometimes neither version.
3. **Run the tests after resolving** — a syntactically clean resolution can be
   semantically wrong, and this is a classic source of reintroduced bugs.
4. Conflicts in generated files: regenerate, do not hand-merge.

Frequent painful conflicts in the same area mean two people own the same code
(`boundaries-and-dependencies`), not that git is difficult.

## Pull requests

- ≤ ~400 changed lines. Larger PRs get approvals, not reviews.
- Description states: what changed, why, how it was verified, what the reviewer
  should scrutinize, and the rollback path.
- Draft PRs for early feedback are cheaper than a surprise at the end.
- Stacked PRs for a large change: each one small, reviewable and mergeable in
  order.

## Recovery

| Situation | Move |
|---|---|
| Committed to the wrong branch | `git cherry-pick` onto the right one, then reset the wrong one |
| Need to undo a pushed commit | `git revert` — never rewrite public history |
| Lost commits after a bad reset/rebase | `git reflog` — almost nothing is truly lost for ~90 days |
| Need one file from another branch | `git restore --source=<ref> -- path` |
| Which commit broke it? | `git bisect run <test command>` — automated, minutes |
| Who changed this line and why? | `git log -L`, `git blame -w -C` (ignores whitespace and moves) |

`git bisect run` is the highest-value command most engineers never use: it
turns "when did this break?" from an afternoon into a coffee break — but only
if commits are atomic and the repository builds at each one. That is what the
discipline above buys.

## Never commit

Secrets, credentials, `.env` files, large binaries, generated artifacts, IDE
state, dependency directories. A secret committed once is compromised: rotate
it **first**, then clean history. Run a secret scanner in pre-commit and in CI —
human vigilance is not a control.

## Exit checklist

- [ ] Each commit is one logical change and builds green
- [ ] Messages explain why, in the imperative, with breaking changes marked
- [ ] Formatting and generated churn are in separate commits
- [ ] Branch is rebased on current trunk before review; no shared history rewritten
- [ ] PR under the size limit with verification and rollback notes
- [ ] Tests run after conflict resolution
- [ ] No secrets, binaries or generated files added
