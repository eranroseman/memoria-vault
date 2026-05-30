---
topic: dashboards
---

# `audit-log` — design summary

**Runtime artifact.** Ships at `00-meta/01-dashboards/audit-log.md` in the [starter vault](https://github.com/eranroseman/memoria-vault) and runs in Obsidian via Dataview; the runtime queries live there. This page covers the design role.

## Mission

The forensic trail for every vault write the policy MCP touched. Spot decisions that need attention: writes blocked at the tool layer (`deny`), dry-run escalations awaiting human action (`dry_run`), writes to review-gated zones (`allow_with_log`). Open when something feels off — a worker behaving strangely, a board card stuck on an unclear reason, or after a scheduled overnight run completes. The audit log file (`00-meta/02-logs/audit.jsonl`, append-only JSONL) is the source of truth; this dashboard is the queryable view.

## What this dashboard is not

- **Not [`drift-watch`](drift-watch.md).** Audit-log records *per-write decisions* (policy MCP outcome per attempted write). Drift-watch records *per-lint-pass findings* (structural-detector outputs). Different cadence, different abstraction.
- **Not a trend view.** [`fleet-health`](fleet-health.md) aggregates audit-log entries into rolled-up metrics (audit deny rate, drift incidents, retry rate). Audit-log itself is the raw event stream — one JSON object per write decision.
- **Not editable.** The audit log is append-only by design. Each entry has `before_hash` and `after_hash` SHA-256s for tamper detection; the [Linter's vault-hash-drift detector](../profiles/linter.md) catches files modified outside this trail.

## Design decisions

- **Reads directly from `00-meta/02-logs/audit.jsonl`** via Dataview's `dv.io.load`. No intermediate aggregation; the dashboard always reflects the latest log state.
- **Recent denies and dry-runs is the action queue.** Sorted newest-first, capped at 30. Anything sitting here for more than a day without a corresponding board card is an unhandled escalation.
- **A deny / out-of-lane-write spike is a security signal, not just forensics.** Memoria ingests untrusted PDFs — an indirect-prompt-injection surface (AgentDojo / InjecAgent show ~24% attack success; ToolEmu shows even "safe" agents act riskily ~24% of the time) — so a sudden rise in policy-MCP denials can indicate an injection attempt, not just operator error. Spike alerting on the deny rate (beyond the newest-first queue) is the intended treatment. See [roadmap/evaluation.md](../../project/roadmap/evaluation.md) (Observability).
- **Review-gated-zone writes are called out explicitly.** Writes to `30-synthesis/01-claims/`, `30-synthesis/02-reference/`, `30-synthesis/03-moc/`, `50-deliverables/` are operationally significant — even when `allow`'d, they should be reviewable. The dashboard's "Writes to review-gated zones" section lists them for periodic audit.
- **The Linter owns rotation.** Weekly rotation of `audit.jsonl` to `00-meta/02-logs/archive/audit-YYYY-WW.jsonl` is the Linter's responsibility; the dashboard queries the current week's file. Archive files are visible to the human but not queried by default.

## Related

- [architecture/policy-mcp.md](../../reference/architecture/policy-mcp.md) — the policy MCP that writes these entries; format and decision protocol
- [`drift-watch`](drift-watch.md) — structural drift findings (different layer, complementary view)
- [`fleet-health`](fleet-health.md) — operational rollups that consume this stream
- [Linter design summary](../profiles/linter.md) — owns audit-log rotation
