---
description: Diagnose and fix a performance problem, measurement first
---

Apply `performance-engineering`.

Input: $ARGUMENTS

1. State what is slow, at which percentile, under what load and data volume.
2. Take a baseline. No baseline, no optimization.
3. Find the bottleneck with a profile or query plan on realistic data.
4. Fix one thing; measure again; record before and after in the PR.
5. Add a CI guard for the budget so the win cannot silently regress.
6. If the added complexity is not justified by the measured gain, revert it.
