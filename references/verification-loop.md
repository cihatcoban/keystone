# Verification loop

How `/verify` and the `verify.stop` hook turn "should work" into evidence
(`CLAUDE.md` §1.1). Use it before calling any change done.

## The phases, and why in this order

| Phase | Answers | Typical commands |
|---|---|---|
| build | Does it compile or bundle at all? | the project's build target |
| types | Do the contracts between modules still hold? | the type checker |
| lint | Does it follow the rules the team wrote down? | linter, formatter check |
| test | Does it behave as specified? | the fast test tier, then slower tiers |
| security | Did it add a known-bad dependency or a secret? | dependency audit, secret scan |
| diff | Did the change lower the bar to get here? | Keystone's bar-protection scan |

Cheap and broad first: a build failure makes every later phase noise. The diff
phase runs last because it judges the change, not the code: a green suite
reached by deleting a test is not green.

## Where the commands come from

From the project, never from habit. `CONSTRAINTS.md` holds a
`## Verification commands` table; each row is one phase and one or more
backticked commands, run from the project root:

```markdown
## Verification commands

| Phase | Command |
|---|---|
| build | `./gradlew assemble` |
| lint | `./gradlew spotlessCheck` |
| test | `./gradlew test` |
| security | `gitleaks detect --no-banner` |
```

Without the table, `verify.py --plan` lists commands found in "Measured by"
cells whose program exists here. Confirm them with the user before running
them with `--inferred`; a command found in a document is a claim, not a fact.

## What counts as evidence

| Evidence | Not evidence |
|---|---|
| The command ran in this checkout and exited 0 | "The tests should pass" |
| The full plan ran after the last edit | One phase run before the last edit |
| A phase that could not run is reported as not run | A skipped phase left out of the report |
| A flaky failure investigated and explained | A rerun until it went green |

The recorded fingerprint makes the last two rows mechanical: any edit after
the run changes the fingerprint, and `verify.stop` notices.

## Results

| Result | Meaning | Next move |
|---|---|---|
| `pass` | Every command passed; no diff findings, or a person accepted them | Report it with the phase list |
| `fail` | A command failed, timed out or could not start | Root cause (`debugging-and-root-cause`), fix, rerun everything |
| `review` | Commands passed; the diff holds bar-protection findings | Fix them, or rerun with `--acknowledge "<reason>"` once a person accepts them |

`--acknowledge` exists for the legitimate cases the scan cannot tell apart,
such as a standalone pull request that lowers a threshold on purpose. The
reason is stored in `.keystone/state/verify.json`; it is never the agent's own
reason.

## Anti-patterns

- **Verifying the wrong thing.** Running a test file that does not import the
  changed code. Read what the command covers before trusting its exit code.
- **Partial runs reported as complete.** `--fail-fast` is for iterating; the
  run that closes the work is the full plan.
- **Fixing the instrument instead of the code.** Raising a timeout, excluding
  a path from coverage, or loosening a linter rule to get past a phase is the
  bar-protection trigger the diff phase exists to catch.
- **Treating the stop gate as noise.** If `verify.stop` fires at the end of a
  turn, the honest report is "changed, not verified" (`CLAUDE.md` §1.10).
