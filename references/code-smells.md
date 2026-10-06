# Code Smells and What They Cost

A smell is a symptom, not a verdict. Fix it when it is in the way of a change
you are already making — not on a sweep.

## Within a function

| Smell | Cost | Move |
|---|---|---|
| Long function (several responsibilities) | Cannot be named, tested or reused | Extract by responsibility |
| Deep nesting | Every level is state the reader carries | Guard clauses, early return |
| Long parameter list | Call sites become unreadable; order errors | Parameter object, or split |
| Boolean parameter selecting behavior | Two functions in a trenchcoat | Split them |
| Flag-driven branching on a type code | Conditional repeats everywhere | Polymorphism or a lookup |
| Magic number/string | Meaning is invisible, drifts | Named constant |
| Comment explaining *what* | Code should say it | Rename, extract |

## Between units

| Smell | Cost | Move |
|---|---|---|
| Feature envy (uses another object's data more than its own) | Logic far from its data | Move the method |
| Inappropriate intimacy (reaches into internals) | Refactoring one breaks the other | Publish an interface |
| Shotgun surgery (one change, many files) | Every change is risky | Consolidate the concept |
| Divergent change (one file, many reasons to change) | Merge conflicts, unclear ownership | Split by reason |
| Message chain (`a.b().c().d()`) | Couples to a whole structure | Ask for what you need |
| Middle man (delegates everything) | Indirection with no value | Inline it |

## Types and data

| Smell | Cost | Move |
|---|---|---|
| Primitive obsession | Nothing prevents the wrong string | Value type |
| Data clump (same 3 fields everywhere) | Missing concept | Extract a type |
| Anemic model | Rules scatter into services | Move behavior to the type |
| Nullable everywhere | Every caller re-checks; some forget | Make absence explicit, or forbid it |
| Mutable shared state | Races, action at a distance | Immutability or single ownership |

## Duplication — read carefully

| Kind | Verdict |
|---|---|
| Same **knowledge** in two places (a rule, a format, a constant) | Unify. Divergence here is a silent bug |
| Same **shape**, different reasons to change | **Leave it.** Unifying creates a parameterized monster that must be split later at higher cost |

Wait for the third occurrence before abstracting. A wrong abstraction is more
expensive than duplication, because it is harder to undo.

## Tests

| Smell | Cost |
|---|---|
| Asserting implementation details | Breaks on every refactor, catches nothing |
| Over-mocking | Passes while the system is broken |
| Conditional logic in a test | A second implementation, untested |
| One test asserting many unrelated things | Failure tells you little |
| Sleep-based waiting | Slow and flaky |
