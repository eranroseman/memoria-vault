---
title: audit-log dashboard
parent: Operational health
nav_order: 2
grand_parent: Dashboards
---

# `audit-log` dashboard

The forensic trail for every vault write the policy MCP touched. Open it when something feels off — a worker behaving unexpectedly, a card stuck with an unclear reason, or after a scheduled overnight run completes.

## What it shows

The dashboard reads directly from `system/logs/audit.jsonl` — the append-only policy MCP event stream. Its primary view is **recent denies and dry-runs**, sorted newest-first and capped at 30. These are the action queue: anything here for more than a day without a corresponding board card is an unhandled escalation.

A second view lists **writes to review-gated zones** (`notes/claims/`, `notes/hubs/`) for periodic audit. Even when these writes were allowed, they warrant occasional review because they represent changes to canonical content.

Further views round out the forensic picture: **per-profile activity over the last 24 hours** (who wrote what, at a glance), **hash drift / tamper detection** (vault-hash mismatches between consecutive entries), **anomalies** (malformed or out-of-order entries in the stream itself), and a **log size** check (when to rotate).

## What it is not

**Not drift-watch.** The audit log records per-write decisions (policy MCP outcome per attempted write). Drift-watch records per-lint-pass structural findings. Different cadence, different abstraction layer.

**Not fleet-health.** Fleet-health aggregates audit log entries into rolled-up trend metrics. The audit log is the raw event stream — one JSON object per write decision.

**Not editable.** The log is append-only by design. Each mutating entry carries `before_hash` and `after_hash` SHA-256s and is paired with a `write_complete` record; the Linter's `audit-unpaired-writes` detector flags a write whose pairing never completed, and this view flags a path whose recorded `after_hash` no longer matches the file. Editing the audit log would break that reversibility.

## Why a spike in denies is a security signal

Memoria ingests untrusted PDFs — a potential indirect prompt injection surface. A sudden rise in policy MCP denials can indicate an injection attempt coaxing an agent toward unauthorized writes, not just operator error. The audit log is the primary place this signal appears; open it after any unexpected agent behavior.

## Log size

The dashboard reads the whole `audit.jsonl` and caps each *view* (e.g. 30 recent denies), so the surface stays bounded even though the log itself is append-only and unbounded in 0.1.0-alpha.1 — rotation (archiving older weeks to `system/logs/archive/`) is a deferred convention, not yet implemented. The audit log's substrate (and the event-field schema) is reference detail — see [Memory substrates](../../../reference/memory.md).

## Related

- [drift-watch dashboard](../structural-health/drift-watch.md) — structural drift findings (complementary layer)
- [fleet-health dashboard](fleet-health.md) — trend aggregations that consume this stream
- [Policy MCP](../../../reference/policy-mcp.md) — the decision protocol and action vocabulary the log records
