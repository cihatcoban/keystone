# Contributing

## Licensing

Keystone is licensed under the Apache License 2.0. Unless you state otherwise,
any contribution you submit is licensed under the same terms (Section 5 of the
license). Do not contribute:

- Text or code **copied** from another project unless its license is compatible
  with Apache-2.0 and you add the required attribution to `NOTICE` — run
  `dependency-and-license-policy` first
- Material your employer has rights over
- Anything whose license you cannot name

## Adding a skill

```bash
python3 scripts/new_skill.py my-skill-name --category architect
```

Then:

1. **Earn the slot.** A new skill must cover work that no existing skill covers.
   Overlap is worse than a gap: two skills that both half-answer a question make
   the router pick badly. Extend an existing skill when you can.
2. **Write the description last and carefully.** It is the only thing the router
   sees. Format: one English sentence saying what it does and when to use it,
   followed by concrete trigger phrases. Aim for ≤ 320 characters: every
   description is injected into every session, and Codex drops all of them
   when the catalog exceeds its budget. `make validate` fails above 500
   characters or when the catalog exceeds its token budget, and warns above
   320.
3. **Body: 400–1400 words.** Longer content belongs in
   `skills/<name>/references/*.md`, loaded on demand.
4. **Stack-agnostic.** No skill assumes a language or framework. Show the
   principle; use pseudocode or two short contrasting examples where a concrete
   form helps. Stack-specific lookups (a language's review traps, a
   framework's idioms) go in a dated `references/*.md` file the body points to,
   never in the body — see
   [ADR-002](docs/adr/ADR-002-stack-specific-references.md).
5. **Every skill ends with an exit checklist** of verifiable statements.
6. **Add an eval case**: `evals/cases/<name>.json`, at least 3 positive and
   2 negative trigger prompts.
7. `make all` must pass with zero errors.

## Adding or changing a command

Edit `commands/<name>.md` only, then run `make adapters`. The Gemini CLI
version in `commands/keystone/` is generated — never edit it by hand.

## Style rules for skill bodies

| Do | Don't |
|---|---|
| Decision tables, thresholds, failure modes | Motivational prose |
| "When NOT to use this" | Implying the skill always applies |
| Name the anti-pattern and its cost | Vague "be careful" |
| Concrete artifacts (file paths, doc shapes) | Abstract advice with no output |

## Commits

`type(scope): summary` in the imperative, ≤ 72 characters. One logical change
per commit. Skill behavior changes bump the version in `CHANGELOG.md`.
