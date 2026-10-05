---
description: Audit dependencies, licenses and personal-data handling
---

Apply `dependency-and-license-policy` and `security-and-threat-modeling`.

1. Vulnerability scan — report high/critical with remediation paths.
2. License inventory against the allow-list, including transitive dependencies
   and any model weights or datasets.
3. Unused and duplicate dependencies.
4. `docs/dependencies.md` accuracy versus the lockfile.
5. `NOTICE` accuracy versus copied third-party material.
6. Personal-data inventory versus what the code actually stores and logs.
7. Output: findings table with severity, owner and suggested action.
