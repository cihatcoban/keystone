# Skill Anatomy

## What a skill is

A procedure an agent can follow to a verifiable end state. Not a tutorial, not
a philosophy, not a reference manual.

```text
skills/<kebab-name>/
  SKILL.md            frontmatter + body (always loaded when selected)
  references/*.md     detail, loaded only when the body points at it
  templates/*         artifacts the skill produces
```

## The two halves have different jobs

| Part | Read when | Job |
|---|---|---|
| `description` | Always, by the router | Get selected at the right moment, and only then |
| Body | After selection | Change what the agent does |

This asymmetry drives everything. A brilliant body with a vague description
never runs. A sharp description with a vague body runs and changes nothing.

### Description

```yaml
description: <what it does and when to use it, one sentence>. Triggers - <phrases people type>.
```

- 80–500 characters hard limit; aim for ≤ 320. All descriptions together form
  a catalog injected into every session — Codex drops the whole catalog when it
  exceeds its budget, so `make validate` caps the total
- Trigger phrases are what a person types **under pressure** — "it's slow",
  "this broke", "should we use a queue" — not the formal name of the discipline
- Include other languages your team works in; routing is lexical enough to care
- Name the boundary with adjacent skills: "for X, use `other-skill`"

### Body

| Section | Why |
|---|---|
| Opening paragraph | The concrete failure prevented. Motivation is what makes an agent comply |
| When to use / when **not** | The "not" half prevents over-triggering as much as the description does |
| Procedure | Numbered, each step with an observable outcome |
| Decision tables | Where judgment is required, give axes and defaults instead of prose |
| Anti-patterns | Name the pattern and its cost |
| Exit checklist | Verifiable statements — this is what converts advice into a gate |

Target 400–1400 words. The validator warns above 1600: long bodies dilute:
every additional paragraph competes with the instructions that matter.

## Why exit checklists matter most

An agent optimizes for appearing finished. A checklist of observable statements
("full suite green", "reproduction test observed failing first") is the
difference between a skill that shapes behavior and one that produces a
confident summary. Write them as things you could verify by looking, never as
intentions.

## Composition

Skills compose; they do not duplicate. `test-driven-development` does not
restate `testing-strategy`, it links. Duplication drifts — two copies of a rule
become two different rules within a year.

Invariants live in `CLAUDE.md`; numbers live in `CONSTRAINTS.md`. A skill that
restates either will contradict it eventually.

## Quality bar for a skill

- Would a competent engineer do this differently without the skill? If not, the
  skill is decoration.
- Does it cover work no other skill covers? Overlap makes routing worse.
- Can an agent verify it followed it? If not, add the observable checks.
- Is it true in five years and in another language? If not, it is a domain
  skill (`examples/domain-pack/`).
