---
title: Session logging
parent: Architecture
grand_parent: Explanation
nav_order: 4
---

# Session logging

Session logging is a system mechanism, not a workflow. The policy MCP records every gated write to an audit log that Git preserves — there is no card, nothing to claim, and no state transition. It runs underneath the card-driven workflows rather than being one of them.

A second, per-session log — a deterministic digest the Linter writes from the audit trail — accumulates alongside it under `system/logs/sessions/`. This page explains the two-log design and why they stay separate.

---

## Two logs in `system/logs/`

These are different artifacts written by different components with different lifecycles. Don't conflate them.

| Log | Path | Writer | Lifecycle |
| --- | --- | --- | --- |
| **Policy MCP audit log** | `system/logs/audit.jsonl` | Policy MCP | Append-only **forever** — never rotated ([ADR-25](../../adr/25-session-logging-two-logs.md)); growth is surfaced by the Linter's `audit-log-size` advisory (50 MB) |
| **Per-session summaries** | `system/logs/sessions/YYYY-MM-DD-HHMM.jsonl` | Linter (`operations/integrity/linter/session_summary.py`, daily cron) | One file per session; never rotated; accumulate indefinitely |

The audit log is what the audit-log and fleet-health [dashboards](../dashboards/README.md) read. The per-session summaries are **deterministic digests** of what happened in a session — the Linter is zero-LLM, so the digest is derived from the audit trail, not narrated: a header (task, profiles, start/end, counts by action and decision) plus one record per touched path (actions, final decision, final `after_hash`). The writer is idempotent (a digested session is never rewritten) and only digests sessions quiet for 24 h, so in-flight work is never summarized early.

---

## Why the two-log separation

The audit log answers "did this write happen and was it authorized?" — it is forensic and append-only. Because each write is hash-paired (the mechanism is owned by [Policy MCP](../../reference/policy-mcp.md)), a write can be reversed and an edit made outside the trail is detectable; the Linter closes the loop over this log with its `audit-unpaired-writes` and `vault-hash-drift` detectors (a legitimate human edit in Obsidian surfaces on the latter too, by design — see [Operations](../operations.md)). Per-session summaries answer "what did the session accomplish?" — they are per-session digests.

Combining them would make the audit log verbose (session detail) and would make session summaries harder to query (mixed with per-write events). Each log has a different reader: the audit log feeds dashboards and tamper detection; session summaries are for the PI reviewing what happened. The decision is [ADR-25](../../adr/25-session-logging-two-logs.md).

---

## Multi-machine safety

Per-session files are named by `YYYY-MM-DD-HHMM`, so files from different machines don't collide during sync. Each machine writes its own session files; the vault accumulates them from all machines without conflict.

---

## Related

- The Linter operation (reads `system/logs/`; runs the integrity checks; writes the session digests): [Operations](../operations.md)
- Session-log granularity (per-session files, not per-action): [Memory substrates](../../reference/memory-substrates.md)
- Audit log (the other log): [Policy MCP](../../reference/policy-mcp.md)
