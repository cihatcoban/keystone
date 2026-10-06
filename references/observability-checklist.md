# Observability Checklist

## Correlation (do this first)

- [ ] Request id generated at the edge if absent, accepted if present
- [ ] Propagated through every call, including queue messages and jobs
- [ ] Present on every log line, span and error report
- [ ] Returned to the client on errors so support can quote it

## Logs

- [ ] Structured key-value, never interpolated prose
- [ ] Each line: correlation id, actor/tenant, operation, outcome, duration
- [ ] Levels mean something; `ERROR` implies a human must act
- [ ] Failure logged once, where handled — not at every layer
- [ ] No secrets, tokens or personal data; redaction at the logger
- [ ] Volume and retention are budgeted, with sampling on high-volume paths

## Metrics

- [ ] Four golden signals per service: latency (histogram), traffic, errors,
      saturation
- [ ] At least one **business** metric per capability — catches outages that
      infrastructure metrics miss
- [ ] Label cardinality bounded; no ids or URLs as labels
- [ ] Percentiles, never averages, for latency

## Traces

- [ ] Every cross-service and cross-process boundary produces a span
- [ ] Spans carry the operation, key attributes and error status
- [ ] Sampling strategy keeps all errors and slow requests

## SLOs

- [ ] SLI measured from the user's perspective, not server-internal success
- [ ] SLO and window written down (e.g. 99.5% over 30 days)
- [ ] Error budget computed; policy for exhaustion agreed in advance
- [ ] Burn-rate alerting: fast burn pages, slow burn tickets

## Alerts

For each alert:

- [ ] Fires on a user-visible symptom, not a cause
- [ ] Requires action now (otherwise it is a dashboard or a ticket)
- [ ] Has a runbook with the first three commands
- [ ] Has fired rarely enough to still be believed
- [ ] Ownership is unambiguous

## Failure of observability itself

- [ ] What happens if the telemetry backend is down? (Never block the request)
- [ ] Is there an alert on "no data received"? Silence must not read as health
