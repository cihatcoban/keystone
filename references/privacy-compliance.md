# Privacy compliance for engineers — KVKK and GDPR

What a system must do mechanically so that Turkey's KVKK (Law No. 6698) and
the EU's GDPR (Regulation 2016/679) can be complied with. Facts checked
2026-10-22; this is engineering guidance, not legal advice — confirm scope,
lawful bases and deadlines with counsel and the official texts
(mevzuat.gov.tr, kvkk.gov.tr, eur-lex.europa.eu) before relying on them.

## The data inventory comes first

Nothing below works without knowing what you hold. Keep a machine-readable
inventory next to the code, reviewed with every schema change:

| Field | Example |
|---|---|
| Data item and where it lives | `users.phone` — primary DB, nightly backup, analytics export |
| Data subject category | customer, employee, visitor |
| Purpose | order delivery |
| Lawful basis | contract performance (KVKK Art. 5/2-c; GDPR Art. 6(1)(b)) |
| Special category? | no — health, biometric, religion and similar are special (KVKK Art. 6; GDPR Art. 9) |
| Retention period and trigger | 10 years after the last order, then destroyed |
| Recipients and transfers | courier API (domestic); email provider (abroad) |

GDPR calls this the record of processing (Art. 30). Under KVKK it feeds the
VERBİS registry entry where registration applies (Art. 16) and the retention
and destruction policy; check the current registration thresholds on the
VERBİS portal rather than in code comments.

## Obligation to mechanism

| Obligation | KVKK | GDPR | What the system needs |
|---|---|---|---|
| Minimization, purpose limitation | Art. 4 | Art. 5 | Every field in the inventory has a purpose; fields without one are not collected |
| Notice at collection | Art. 10 (aydınlatma) | Art. 13–14 | The notice text versioned with the form that collects the data |
| Consent where it is the basis | Art. 5/1 (açık rıza) | Art. 6(1)(a), 7 | Consent stored per purpose with timestamp, text version and withdrawal path |
| Access and portability | Art. 11 | Art. 15, 20 | One query that exports a person's data in a structured format |
| Correction and erasure | Art. 7, 11 | Art. 16, 17 | Erasure that reaches replicas, search indexes, caches and analytics; backups expire on schedule |
| Retention and destruction | Art. 7 and the destruction regulation (periodic destruction) | Art. 5(1)(e) | A scheduled job that deletes or anonymizes by retention rule, with a log of what it destroyed |
| Security | Art. 12 | Art. 32 | Encryption in transit and at rest for sensitive data, least-privilege access, access logs |
| Breach notification | Art. 12/5 — the Board, within 72 hours of learning (Board principle decision); data subjects within a reasonable time | Art. 33 — the authority within 72 hours; Art. 34 — data subjects without undue delay when high risk | Detection, an incident runbook with these clocks, and logs that show what was accessed |
| Transfer abroad | Art. 9 as amended by Law No. 7499: adequacy, appropriate safeguards (including standard contracts, notified to the Authority within five business days of signing), or listed exceptions | Art. 44–49: adequacy, standard contractual clauses, BCRs, derogations | Inventory of every processor and region; no new third-party API carrying personal data without this check |
| Impact assessment | No general equivalent; assess high-risk processing anyway | Art. 35 (DPIA) | A design-review step for new processing of special categories or at scale |
| Privacy by design | Implied by Art. 12 | Art. 25 | Defaults that collect less; pseudonymous ids in analytics and logs |

## Engineering defaults

- **Logs, traces, error reports and LLM prompts hold no personal data** unless
  the inventory says so and access is restricted. Redact at the sink.
- **Analytics gets pseudonymous ids**, with the mapping table held separately.
- **Test and staging data are synthetic** or irreversibly anonymized; a
  production copy in staging is a transfer and a breach waiting to happen.
- **Every third-party SDK or API** that receives personal data is a recipient
  in the inventory, and possibly a transfer abroad.
- **Erasure is tested**: a test creates a person, erases them, and asserts no
  table, index or export still returns them.

## Review questions for a change that touches personal data

1. Which inventory rows does it add or change, and who reviewed the basis?
2. Does any new field, log line, event or prompt carry personal data?
3. Does data now leave the country or reach a new processor?
4. Do erasure, export and retention still reach the new storage?
5. Would we know, from logs, what an attacker read through this path?
