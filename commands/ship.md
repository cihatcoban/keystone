---
description: Release readiness — gates, rollout, rollback, observation
---

Apply `release-engineering`, with `observability-and-slos` for the watch plan.

1. Gates green; build versioned and reproducible.
2. Migration phase compatible with the currently running version; rollback
   tested against a migrated database.
3. Rollout strategy chosen, with the numeric rollback trigger written down.
4. Telemetry for the new behavior exists and is verified after deploy.
5. Changelog written for consumers; version bump matches the change class.
6. Name the three signals to watch and for how long, and who owns the decision.
7. Write the post-release canary list (`release-engineering`, "Post-release
   verification"): version serving, synthetic journeys, error/latency against
   a baseline, new log signatures, one business signal — each with its time
   and rollback threshold.
