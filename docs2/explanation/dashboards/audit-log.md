# `audit-log` dashboard

The forensic trail for every vault write the policy MCP touched. Open it when something feels off — a worker behaving unexpectedly, a card stuck with an unclear reason, or after a scheduled overnight run completes.

## What it shows

The dashboard reads directly from `00-meta/02-logs/audit.jsonl` — the append-only policy MCP event stream. Its primary view is **recent denies and dry-runs**, sorted newest-first and capped at 30. These are the action queue: anything here for more than a day without a corresponding board card is an unhandled escalation.

A second view lists **writes to review-gated zones** (`30-synthesis/01-claims/`, `30-synthesis/02-reference/`, `30-synthesis/03-moc/`, `50-deliverables/`) for periodic audit. Even when these writes were allowed, they warrant occasional review because they represent changes to canonical content.

## What it is not

**Not drift-watch.** The audit log records per-write decisions (policy MCP outcome per attempted write). Drift-watch records per-lint-pass structural findings. Different cadence, different abstraction layer.

**Not fleet-health.** Fleet-health aggregates audit log entries into rolled-up trend metrics. The audit log is the raw event stream — one JSON object per write decision.

**Not editable.** The log is append-only by design. Each entry carries `before_hash` and `after_hash` SHA-256s; the Linter's `vault-hash-drift` detector catches files modified outside this trail. Editing the audit log would break the chain.

## Why a spike in denies is a security signal

Memoria ingests untrusted PDFs — a potential indirect prompt injection surface. A sudden rise in policy MCP denials can indicate an injection attempt coaxing an agent toward unauthorized writes, not just operator error. The audit log is the primary place this signal appears; open it after any unexpected agent behavior.

## Log rotation

The Linter rotates `audit.jsonl` weekly to `00-meta/02-logs/archive/audit-YYYY-WW.jsonl`. The dashboard queries the current week's file. Archive files accumulate in `00-meta/02-logs/archive/` and are not queried by default.

## Related

- [reference/architecture/policy-mcp.md](../../reference/architecture/policy-mcp.md) — the decision protocol and action vocabulary the log records
- [explanation/dashboards/drift-watch.md](drift-watch.md) — structural drift findings (complementary layer)
- [explanation/dashboards/fleet-health.md](fleet-health.md) — trend aggregations that consume this stream
