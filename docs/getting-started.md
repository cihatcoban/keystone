# Getting Started

## 1. Install

```bash
git clone https://github.com/cihatcoban/keystone.git
cd keystone
claude --plugin-dir "$(pwd)"
```

Verify: in a new session, ask *"which skill should I use to add a new external
API call?"* The router should point at `distributed-systems-and-resilience` and
`api-and-contract-design`. If it answers generically, the plugin is not loaded.

## 2. Set up a project to use it

In the project you are working on, not in Keystone:

```
/onboard        # discovers the stack, writes the agent's operating context
/constraints    # fills CONSTRAINTS.md with real numbers
```

`/onboard` runs the commands rather than assuming them, so the context it
writes is true on the day it is written. `/constraints` measures your current
values first and installs ratchets where the target is far away — you do not
have to hit 70% coverage tomorrow.

These two produce the files that make every later skill enforceable. Skipping
them leaves the agent reasoning from generic defaults.

## 3. The daily loop

```
/spec  →  /design (only if a choice is costly to reverse)  →  /plan
       →  /build (per task)  →  /review  →  /ship
```

Between those: `/debug` when something breaks, `/perf` when something is slow,
`/secure` before anything touching auth or untrusted input, `/audit` before
adding a dependency, `/incident` when production is unhappy.

You do not have to invoke commands — skills also fire from how you describe the
work. The commands are for when you want the whole procedure applied
deliberately.

## 4. What good use looks like

| Instead of | Say |
|---|---|
| "add caching" | "this endpoint is slow" — `/perf` will find whether caching is even the answer |
| "write tests for this file" | "what should we test here?" — `testing-strategy` starts from risk, not from coverage |
| "make this cleaner" | "I need to change this code and it has no tests" — you get a safety net first |
| "use microservices" | "should this be a separate service?" — the decision gets its forces written down |

## 5. Making it yours

- **Adjust the numbers.** `CONSTRAINTS.md` defaults are starting points. A
  prototype and a payment system deserve different bars.
- **Add invariants.** `CLAUDE.md` §1 is where "we never do X here" belongs.
- **Write a domain pack** when a procedure is specific to your product
  (`examples/domain-pack/`).
- **Fix routing, not bodies.** A skill that does not fire needs description
  words, not more content.

## Troubleshooting

**A skill never fires.** Its description lacks the words you type. Add them,
add the prompt to `evals/cases/<name>.json`, run `make triggers`.

**The wrong skill fires.** Two descriptions overlap. Sharpen both and state the
boundary in each ("for X, use `other-skill`").

**The agent ignores the constraints.** `CONSTRAINTS.md` must be in the project
root, not in Keystone. Check that thresholds are filled in — a blank threshold
is unenforceable.

**Answers get worse in a long session.** Context pollution, not model fatigue.
See `context-engineering` — restate the goal, or start a fresh session with a
written handoff.
