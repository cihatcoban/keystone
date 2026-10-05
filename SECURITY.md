# Security Policy

## Scope

This repository contains process documentation and tooling scripts. It holds
no production code and no credentials. The security surface is:

- `scripts/*.py` — run locally and in CI
- `hooks/*.sh` — optional, run at agent session start on hosts without native
  skill routing
- Anything a consumer copies out of `templates/`

## Reporting

Report a suspected issue privately to the repository owner. Do not open a
public issue for anything exploitable.

## Guarantees this repository tries to keep

- No secret values anywhere, including examples. `.env.example` files list key
  names only.
- Scripts read files and print findings; they do not execute repository
  content, make network calls, or write outside the repository.
- CI runs a secret scanner on every pull request.

## For projects that install Keystone

The `security-and-threat-modeling` skill and
`references/threat-model-checklist.md` define the expected practice. Keystone
does not grant your project any security property by itself — it describes the
work that does.
