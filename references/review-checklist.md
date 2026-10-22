# Review Checklist

Compact form of `code-review-and-quality`. Work top to bottom; the first
section costs two minutes and prevents the most damage.

## 0. Bar protection (first, always)

- [ ] New suppression without justification + link
- [ ] Test deleted, skipped, or assertion weakened
- [ ] `CONSTRAINTS.md` threshold lowered inside a feature change
- [ ] `catch {}` / `except: pass` added
- [ ] Stub presented as complete
- [ ] Fixture or golden file changed together with the logic that produces it

## 1. Scope

- [ ] Diff matches its description; nothing unrelated rides along
- [ ] Under ~400 changed lines, or split with a reason
- [ ] Project tools ran on the diff; `references/review-lenses.md` applied for
      each language in it

## 2. Correctness

- [ ] Boundaries: empty, one, many, max, off-by-one
- [ ] Absent values: null, missing field, zero, empty string
- [ ] Error paths return something the caller can act on
- [ ] Read-modify-write on shared state is atomic, versioned or locked
- [ ] Safe if executed twice

## 3. Failure behavior

- [ ] Every external call has a timeout and a defined failure outcome
- [ ] No half-updated state possible on partial failure
- [ ] Failure is observable: logged once, with context, countable
- [ ] Change is reversible; if it deletes or migrates, the undo is stated

## 4. Design

- [ ] Respects the dependency rule; no boundary crossed silently
- [ ] Abstraction earned by real use, not speculative
- [ ] No business rule in a controller, job or view
- [ ] Names would make sense to a newcomer

## 5. Security

- [ ] Untrusted input validated at the boundary; queries parameterized
- [ ] Object-level authorization at the data layer
- [ ] No secrets or personal data in code, logs, errors or client bundles

## 6. Performance

- [ ] No query inside a loop
- [ ] No unbounded result set, allocation or concurrency
- [ ] Hot-path work justified; budget unaffected

## 7. Tests

- [ ] Would fail if the implementation were wrong (mutate one line mentally)
- [ ] Assert behavior, not implementation
- [ ] Boundaries and error paths, not only the happy path
- [ ] No sleep, real clock, network or order dependence in the fast tier

## Verdict

`APPROVE` · `APPROVE AFTER FIXES` · `REQUEST CHANGES (reason)` — exactly one.
