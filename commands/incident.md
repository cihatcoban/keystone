---
description: Run a production incident, or write the postmortem
---

Apply `incident-response`.

If the incident is live:
1. Mitigate first — flag off, roll back, fail over, shed load. Do not diagnose
   a burning system.
2. Name roles; one person changes production.
3. Capture evidence before any restart.
4. Communicate on a 30-minute cadence in user terms.

If writing the postmortem:
1. Timeline of facts with timestamps, no interpretation.
2. Contributing factors, not a single cause. "Human error" is a prompt, not a
   root cause.
3. What went well, what made it worse.
4. Action items with owner, date and priority — each one verifiable.
5. Update the runbook and the alert with what was learned.
