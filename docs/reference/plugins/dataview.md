---
topic: plugins
---

# dataview

Load-bearing settings:

- `enableJs: true` — required for the `dataviewjs` blocks in [audit-log.md](../../explanation/dashboards/audit-log.md) and [fleet-health.md](../../explanation/dashboards/fleet-health.md), which read external files (`audit.jsonl`, `lane-metric` notes).
- `refreshEnabled: true` — without this, queries don't update as notes change.
- `refreshInterval: 2500` (ms) — default is fine. Going lower hurts performance on large vaults.
