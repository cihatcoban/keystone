# Example: a domain skill pack

Keystone is domain-neutral on purpose — it describes engineering practice, not
your product. Product-specific procedure belongs in a **domain pack** that
layers on top.

This directory is a worked example, drawn from a real system (multi-source
public-tender matching: ingesting notices from many portals in several
languages, and scoring them against company profiles). It exists to show the
shape, not to be installed.

## Why a separate pack

| Core skill | Domain skill |
|---|---|
| `api-and-contract-design` — how to design any contract | `tender-source-onboarding` — the eight gates *this* product requires before a new source goes live |
| `data-modeling-and-storage` — general schema practice | Which canonical fields this domain has and what "normalized" means here |
| `testing-strategy` — levels and data | Which fixtures this domain must keep, and why live sources are never called in tests |

Core skills survive a change of product. Domain skills encode decisions that
are only true for one system, and they belong beside that system's code so they
version with it.

## Rules for a domain pack

1. **Same file format**, same authoring rules (`skill-authoring`).
2. **Name after the domain noun** (`tender-source-onboarding`,
   `invoice-reconciliation`), not the generic verb — otherwise it competes with
   a core skill for routing.
3. **Cite core skills, never contradict them.** A domain skill that needs to
   override an invariant is a project-level `CLAUDE.md` decision instead.
4. **Live in the product repository**, not in Keystone.
5. **Encode decisions, not tutorials.** "Sources are onboarded through these
   eight gates" is a skill; "how HTTP works" is not.

## Installing both

```jsonc
// the product's .claude-plugin/plugin.json
{ "skills": ["./vendor/keystone/skills", "./skills"] }
```

Core skills answer general questions; domain skills answer the ones only this
product can.
