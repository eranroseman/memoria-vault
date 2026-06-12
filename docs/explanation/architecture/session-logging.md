---
title: Session logging
parent: Architecture
nav_order: 5
---

# Session logging

Session logging is a system mechanism, not a workflow. The policy MCP records every gated write to an audit log that Git preserves — there is no card, nothing to claim, and no state transition. It runs underneath the card-driven workflows rather than being one of them.

A second, narrative per-session log is *designed but not yet built* in 0.1.0-alpha.1 (see the table below). This page explains the two-log design and why they stay separate.

---

## Two logs in `system/logs/`

These are different artifacts written by different components with different lifecycles. Don't conflate them.

| Log | Path | Writer | Lifecycle |
| --- | --- | --- | --- |
| **Policy MCP audit log** | `system/logs/audit.jsonl` | Policy MCP | Append-only; unbounded (no rotation in 0.1.0-alpha.1) |
| **Per-session summaries** *(deferred — not built in 0.1.0-alpha.1)* | `system/logs/sessions/YYYY-MM-DD-HHMM.jsonl` | designed: a Linter-written summary of Hermes activity | One file per session; never rotated; accumulate indefinitely |

The audit log — the shipped log — is what the audit-log and fleet-health [dashboards](../dashboards/README.md) read. The per-session summaries are the *designed* narrative record of what happened in a session (which skills ran, what decisions were made, which cards were advanced); no component writes them yet.

---

## Why the two-log separation

The audit log answers "did this write happen and was it authorized?" — it is forensic and append-only, and each write is **hash-paired**: every mutating entry records a `before_hash` and `after_hash` and is matched by a `write_complete` record, so a write can be reversed and an edit made outside the trail is detectable (this is per-write pairing, not a cross-entry hash chain). Per-session summaries answer "what did the session accomplish?" — they are narrative and per-session.

Combining them would make the audit log verbose (session narrative) and would make session summaries harder to query (mixed with per-write events). Each log has a different reader: the audit log feeds dashboards and tamper detection; session summaries are for the researcher reviewing what happened. The decision — and the deferred status of the narrative log — is [ADR-25](../../adr/25-session-logging-two-logs.md).

---

## Multi-machine safety

Per-session files are named by `YYYY-MM-DD-HHMM`, so files from different machines don't collide during sync. Each machine writes its own session files; the vault accumulates them from all machines without conflict.

---

## Related

- The Linter engine (reads `system/logs/`; runs the `audit-unpaired-writes` integrity check): [Engines](../engines/README.md)
- Session-log granularity (per-session files, not per-action): [Memory substrates](../../reference/memory.md)
- Audit log (the other log): [Policy MCP](../../reference/policy-mcp.md)
