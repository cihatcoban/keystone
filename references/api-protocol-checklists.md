# API Protocol Checklists

Lookup for `api-and-contract-design` (see
[ADR-002](../docs/adr/ADR-002-stack-specific-references.md)): how the skill's
rules — stable errors, idempotency, bounded lists, compatibility, mechanical
contract checks — are met in each protocol, and where each protocol breaks
them quietly. HTTP/REST defaults are in `references/http-api-conventions.md`.

**Checked against:** the GraphQL specification, Protocol Buffers (proto3 and
editions) with gRPC status codes, CloudEvents 1.0, AsyncAPI 3, RFC 9457 — on
2026-10-22. For a protocol not listed, apply the skill directly and say this
lookup was missing.

## GraphQL

**Compatibility traps**

- Output field non-null → nullable is **breaking** (clients did not handle
  null); nullable → non-null is safe. For inputs it is the reverse: a new
  required argument or input field without a default is breaking.
- Adding an enum value breaks clients that switch exhaustively. State in the
  schema documentation that clients must handle unknown values, as with REST.
- Remove nothing without `@deprecated(reason: "…")`, a published date, and
  field-level usage data showing it is unused.

**Errors**

- Expected domain failures belong **in the schema**: a result union or a
  payload with typed `userErrors` carrying stable codes. The top-level
  `errors` array is for the unexpected, with `extensions.code` set.
- Partial results are normal; document which fields may be null because a
  sibling resolver failed.

**Shape and limits**

- Mutations take one input object and return a payload type, so both can grow.
- Lists are connections with cursors and a capped `first`.
- Batch data loading per request in resolvers — one query per item is N+1 by
  construction.
- Bound every query: depth, cost/complexity, and execution time. First-party
  clients use persisted or allow-listed operations; decide deliberately
  whether production introspection is public.
- Authorize per object in resolvers or the data layer, not only on the root
  field — nested fields are reachable from many roots.

**Mechanical check:** schema diff in CI against the deployed schema, failing on
breaking changes; operation validation of known client queries against the
new schema.

## gRPC / Protocol Buffers

**Compatibility traps**

- Field **numbers** are the contract. Never reuse or renumber one; mark removed
  numbers and names `reserved`.
- Changing a field's type is breaking except in narrow wire-compatible cases;
  renaming is wire-safe but breaks the JSON mapping and generated code.
- Every enum starts with a `…_UNSPECIFIED = 0` value; zero is what a missing
  field decodes to.
- When "absent" differs from the zero value, declare presence (`optional` or a
  wrapper type) — otherwise `0`, `""` and "not sent" are indistinguishable.
- Version by package (`acme.billing.v1`); a breaking change is a new package.

**Errors and calls**

- Map domain failures to canonical status codes — `INVALID_ARGUMENT`,
  `NOT_FOUND`, `ALREADY_EXISTS`, `FAILED_PRECONDITION`, `PERMISSION_DENIED` —
  with structured details carrying the stable machine code. `UNAVAILABLE`
  means retryable; most others do not.
- Every call has a deadline, and the server propagates it downstream and stops
  work when it passes.
- Retry policy only for idempotent methods and retryable codes, with a
  ceiling.
- Streams: cap message size, define what a client does after a mid-stream
  failure (resume token or restart), and respect flow control.

**Mechanical check:** a breaking-change checker on `.proto` files in CI
against the last released version; lint for naming and the zero enum value.

## Events and messages

**Contract**

- Schema in a registry or in the repository, with a declared compatibility
  mode (backward, forward or full) enforced on every publish or in CI.
- An envelope on every event: `event_id`, `type`, `version`, `occurred_at`,
  source, correlation id. CloudEvents is a ready-made envelope.
- Document channels, keys and payloads (AsyncAPI) — consumers are often
  unknown to the producer.

**Delivery**

- Assume at-least-once: consumers deduplicate on `event_id`; producers write
  the event and the state change atomically (outbox,
  `distributed-systems-and-resilience`).
- Ordering exists only per partition key. Key by the aggregate id when
  per-aggregate order matters; never assume global order.
- Poison messages: bounded retries, then a dead-letter queue that alerts, plus
  a tested replay path.
- Old versions are replayed for years: upcast them on read rather than
  rewriting history.
- Events are retained and copied: no secrets, and minimal personal data
  (`references/privacy-compliance.md`).

## Webhooks

**Sending**

- Sign every delivery: HMAC over a timestamp and the raw body, with a
  documented verification recipe and key rotation.
- Include a delivery id; retry with exponential backoff on a published
  schedule; disable an endpoint after a stated number of consecutive failures
  and notify its owner.
- Short timeouts; ask receivers to acknowledge quickly and process
  asynchronously.
- Validate registered URLs against SSRF: no private, link-local or internal
  ranges, re-checked at delivery time (`references/threat-model-checklist.md`).

**Receiving**

- Verify the signature over the **raw** body before parsing, with a
  constant-time comparison; reject timestamps older than the stated window
  (minutes, not hours) to block replay.
- Deduplicate on the delivery id; treat the payload as a hint and fetch the
  authoritative state when it matters.
