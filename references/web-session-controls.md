# Web and Session Controls

Detail for `security-and-threat-modeling`: the browser-facing and
authentication controls that a threat model names and a review checks, with
the test that fails when each one is missing. Use the project's framework for
the mechanism; use this file for the values and the test.

**Checked against:** OWASP Cheat Sheet Series — Password Storage, Session
Management, Cross-Site Request Forgery Prevention — on 2026-10-23. Prefer the
current cheat sheet when it disagrees with this file, and update this file.

## Passwords

| Choice | Minimum parameters | When |
|---|---|---|
| Argon2id | 19 MiB memory, 2 iterations, parallelism 1 (or another listed equivalent) | Default |
| scrypt | N = 2^17, r = 8, p = 1 | Argon2id unavailable |
| bcrypt | Work factor ≥ 10; reject passwords over 72 bytes | Legacy systems only |
| PBKDF2-HMAC-SHA256 | 600,000 iterations | FIPS-140 compliance required |

- Store the algorithm and parameters with each hash (PHC string format), so
  old and new hashes coexist; re-hash with current parameters on the next
  successful login.
- A pepper is optional defense in depth: keep it in the secret manager, never
  beside the hashes.
- Use the platform's vetted implementation; never a hand-rolled or fast hash.

**Test:** the stored value names the algorithm and parameters; logging in with
a legacy hash rewrites it with current parameters.

## Sessions and cookies

- Session identifiers come from the framework's cryptographically secure
  generator — at least 64 bits of entropy; 128 if you generate them yourself.
- Cookie attributes: `Secure`, `HttpOnly`, `SameSite=Strict` or `Lax` set
  explicitly, no `Domain`, the narrowest `Path`. The `__Host-` name prefix
  enforces `Secure`, no `Domain` and `Path=/`.
- Issue a new session identifier at login and at every privilege change, and
  destroy the old one (session fixation).
- Idle timeout enforced on the server — minutes for high-value applications —
  plus an absolute lifetime regardless of activity.
- Logout invalidates the session **on the server**; deleting the cookie does
  not invalidate a stolen copy. Send `Cache-Control: no-store` on responses
  that carry session data.

**Tests:** the pre-login session identifier is rejected after login; a session
identifier replayed after logout gets 401; a session idle past the timeout is
rejected.

## Cross-site request forgery

- Stateful applications: a synchronizer token per session or request.
- Stateless applications: a **signed** double-submit cookie bound to the
  session (HMAC); the unsigned variant is not a defense.
- Check `Sec-Fetch-Site` on state-changing requests, falling back to
  `Origin` / `Referer` when the header is absent.
- `SameSite` is defense in depth, not the defense.
- A required custom request header protects JavaScript-only API endpoints only
  while CORS stays strict.
- `GET` never changes state.

**Test:** a cross-site `POST` without a valid token is rejected with 403 and
changes nothing.

## Cross-origin resource sharing

- Allow-list exact origins. Never reflect the request's `Origin` back together
  with `Access-Control-Allow-Credentials: true` — that grants every site the
  user's session.
- Allow only the methods and headers the API uses.

**Test:** a request with `Origin: https://attacker.example` receives no
`Access-Control-Allow-Origin` header.

## Response headers

| Header | Purpose |
|---|---|
| `Strict-Transport-Security` | HTTPS only on later visits; add `includeSubDomains` when every subdomain is HTTPS |
| `Content-Security-Policy` | Limits script sources; `frame-ancestors` controls who may frame the page |
| `X-Content-Type-Options: nosniff` | Stops the browser guessing content types |
| `Referrer-Policy` | Keeps paths and tokens in URLs from leaking to other sites |

**Test:** an integration test asserts each header on a representative page
and API response; a CSP violation report endpoint, if used, is monitored.

## Authentication endpoints

- Rate-limit login, password reset and second-factor verification per account
  and per source.
- Answer "unknown user" and "wrong password" identically, in content and as
  closely as practical in timing, to avoid account enumeration.
- Password reset tokens: random, single-use, short-lived; resetting ends the
  user's other sessions.

**Tests:** the limit returns 429 and the account still works for its owner
afterwards; responses for an unknown user and a wrong password are identical.

## File uploads

- Allow-list file types and check the content, not only the extension or the
  client-sent content type.
- Store under generated names outside the web root; serve with
  `Content-Disposition: attachment` unless rendering is intended.
- Enforce a size limit before the whole body is read.

**Test:** an upload of an HTML or SVG file renamed `.png` is rejected or served
as a download, never rendered inline from your origin.
