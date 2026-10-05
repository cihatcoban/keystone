# Threat Model Checklist (STRIDE)

Ten minutes, written down, per non-trivial change.

## Frame
1. What are we protecting? (data, money, availability, reputation)
2. Who attacks it? (anonymous outsider, other tenant, insider, compromised
   dependency, automated scanner)
3. Where does data cross a trust boundary?
4. What is the worst outcome of each boundary being abused?

## Entry points to enumerate
HTTP handlers · webhooks · queue consumers · scheduled jobs · file uploads ·
CLI arguments · environment and config · deserializers · third-party callbacks ·
admin interfaces · database seeds and fixtures · anything an LLM can invoke

## STRIDE prompts

**Spoofing** — Can someone claim another identity? Is every request
authenticated? Are service-to-service calls authenticated, or trusted by
network position alone? Are tokens validated (signature, audience, expiry)?

**Tampering** — Can a client modify data it should not? Are client-supplied ids
authorized? Are prices, totals or roles ever taken from the request? Is
integrity protected in transit and at rest where it matters?

**Repudiation** — Can we reconstruct who did what? Are security-relevant events
logged with actor, action, timestamp? Are those logs tamper-resistant?

**Information disclosure** — What do errors reveal? Stack traces, internal ids,
existence of a record (enumeration)? Is personal data in logs, analytics, LLM
prompts or client bundles? Are storage and backups access-controlled?

**Denial of service** — Are request size, array length, string length, nesting
depth, regex complexity and parse time bounded? Is there a rate limit per
identity? Can one tenant exhaust shared capacity? Is any operation
unboundedly expensive?

**Elevation of privilege** — Is authorization checked at the data layer for
every access? Are object-level checks present (can user A act on user B's
record)? Is deny-by-default in place for new routes? Can a low-privilege path
reach a high-privilege operation indirectly (a job, a webhook, a tool call)?

## Output
| Threat | Entry point | Likelihood | Impact | Mitigation | Status |
|---|---|---|---|---|---|

Accepted risks are recorded with who accepted them. Unrecorded acceptance is
just an unnoticed vulnerability.
