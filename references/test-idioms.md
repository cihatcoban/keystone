# Test Idioms

Lookup for `test-driven-development` and `testing-strategy` (see
[ADR-002](../docs/adr/ADR-002-stack-specific-references.md)): how the skills'
rules — table-driven boundary cases, one focused run per RED, no real clock,
generated inputs for invariants — look in a given language. It adds no rules.
The project's existing tests win over this file: copy their runner, layout and
helpers first (`CLAUDE.md` §3).

**Checked on 2026-10-23:** Go 1.25 `testing/synctest`, .NET
`FakeTimeProvider` and Tokio `start_paused` against their documentation; the
other entries are long-stable APIs of the tools named. Confirm versions during
stack discovery. For a language not listed, apply the skills and say this
lookup was missing.

| Language | Table of cases | Focused run (for RED) | Time under control | Generated inputs |
|---|---|---|---|---|
| TypeScript / JavaScript | `test.each` (Vitest, Jest) | The test file, plus `-t "<name>"` | `vi.useFakeTimers()` / `jest.useFakeTimers()`; inject `now` | fast-check |
| Python | `@pytest.mark.parametrize` | `pytest path/to/test_x.py::test_name` or `-k` | Inject a clock; time-machine or freezegun where the code reads the system clock | Hypothesis |
| Go | A slice of cases, each run with `t.Run(name, …)` | `go test ./pkg -run 'TestX/case'` | `testing/synctest` (fake clock inside the bubble, Go 1.25+); or inject a clock | Native fuzzing: `go test -fuzz` |
| Java | JUnit 5 `@ParameterizedTest` with `@CsvSource` or `@MethodSource` | The build's test filter (`--tests` in Gradle, `-Dtest=` in Maven) | Inject `java.time.Clock`; `Clock.fixed(…)` in tests | jqwik |
| Kotlin | JUnit 5 parameterized tests, or Kotest data-driven tests | As for Java | Coroutines: `runTest` runs delays on virtual time; inject `Clock` otherwise | Kotest property testing |
| C# / .NET | xUnit `[Theory]` + `[InlineData]` / `[MemberData]`; NUnit `[TestCase]` | `dotnet test --filter "FullyQualifiedName~X"` | Depend on `TimeProvider`; `FakeTimeProvider` (`Microsoft.Extensions.TimeProvider.Testing`) in tests | FsCheck |
| Rust | A slice of cases in one test, or `rstest` `#[case]` | `cargo test <name_filter>` | Inject a clock; Tokio: `#[tokio::test(start_paused = true)]` (needs the `test-util` feature) | proptest |
| Swift | Swift Testing `@Test(arguments: …)` — one case per argument | `swift test --filter <name>` | Inject a clock rather than reading `Date()` | — |

## Rules that hold in every row

- **Each case is named.** A table row that fails reports which row; an unnamed
  loop reports "assertion failed at line 40".
- **The focused run is the RED.** Record its failing assertion in the evidence
  map; the full suite is the last GREEN, never the first.
- **Fake time is injected, not patched globally,** wherever the code allows it.
  Global patching leaks between tests and hides the dependency; patch only
  code you cannot change.
- **Generated inputs assert an invariant,** not an example: "encoding then
  decoding returns the input", "the total never goes negative". Keep the seed
  of any failure as a fixed regression case.
- **Async tests await the work they start.** A test that finishes before its
  promise, task or goroutine is a test that cannot fail.
