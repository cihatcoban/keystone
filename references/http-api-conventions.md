# HTTP API Conventions

Defaults for a new HTTP API. Deviate deliberately and write down why.

## Resources
- Plural nouns from the domain glossary: `/invoices`, `/invoices/{id}`
- Nest only one level; beyond that, use a query parameter
- Actions that are not CRUD: a sub-resource (`POST /orders/{id}/cancellation`)
  rather than a verb in the path

## Methods and status
| Method | Semantics | Success |
|---|---|---|
| GET | Safe, idempotent, cacheable | 200, 404 |
| POST | Create or non-idempotent action | 201 + `Location`, 202 for async |
| PUT | Full replace, idempotent | 200/204 |
| PATCH | Partial update | 200/204 |
| DELETE | Idempotent removal | 204; 404 or 204 on repeat — pick one and document it |

4xx = the caller must change something. 5xx = the caller may retry. **Never
return 200 with an error body** — it breaks every generic client, retry policy
and monitor.

## Errors
```json
{ "error": { "code": "INSUFFICIENT_FUNDS", "message": "human-readable",
             "field": "amount", "retryable": false,
             "correlation_id": "01H..." } }
```
Stable machine codes; prose may change, codes may not. Consider RFC 9457
(`application/problem+json`) for public APIs.

## Collections
- Always paginated, always with a maximum. Cursor pagination for large or
  changing sets; offset only for small stable ones.
- Response envelope: `{ "data": [...], "next_cursor": "...", "total": 123? }`
  — `total` only if you can produce it cheaply.
- Filtering and sorting are part of the contract: allow-list fields, do not
  pass through arbitrary expressions.

## Writes
- Idempotency: accept an `Idempotency-Key` header on POST; store the response
  against the key and replay it on retry.
- Concurrency: `ETag` + `If-Match` for conditional updates; return 412 on
  mismatch.
- Validation errors return **all** failures at once, with field attribution.

## Async operations
Return `202` with a status resource (`/operations/{id}`). Never hold a request
open for a long job; never make the client poll an unbounded endpoint without a
documented interval.

## Cross-cutting
- Versioning: `/v1/` in the path for public APIs; support N-1 with a published
  sunset date.
- Correlation: accept and propagate a request id header; return it on errors.
- Rate limits: `429` with `Retry-After`, plus limit/remaining/reset headers.
- Timestamps: RFC 3339 UTC. Money: minor units or decimal string, never float.
- Compression and caching headers set deliberately, not by accident.
