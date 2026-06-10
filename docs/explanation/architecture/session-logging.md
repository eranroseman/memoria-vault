---
title: Session logging
parent: Architecture
nav_order: 5
---

# Session logging

Session logging is a system mechanism, not a workflow. Every agent session produces a per-session log that Git preserves — there is no card, nothing to claim, and no state transition. It runs underneath the card-driven workflows rather than being one of them.

---

## Two logs in `system/logs/`

These are different artifacts written by different components with different lifecycles. Don't conflate them.

| Log | Path | Writer | Lifecycle |
| --- | --- | --- | --- |
| **Per-session summaries** | `system/logs/sessions/YYYY-MM-DD-HHMM.jsonl` | Linter engine (summarizes Hermes raw activity) | One file per session; never rotated; accumulate indefinitely |
| **Policy MCP audit log** | `system/logs/audit.jsonl` | Policy MCP | Append-only; rotated weekly by the Linter engine |

The audit log is what the audit-log and fleet-health [dashboards](../dashboards/README.md) read. The per-session summaries are the narrative record of what happened in a session — which skills ran, what decisions were made, which cards were advanced.

---

## Why the two-log separation

The audit log answers "did this write happen and was it authorized?" — it is forensic, append-only, and hash-chained. Per-session summaries answer "what did the session accomplish?" — they are narrative, per-session, and not hash-chained.

Combining them would make the audit log verbose (session narrative) and would make session summaries harder to query (mixed with per-write events). Each log has a different reader: the audit log feeds dashboards and tamper detection; session summaries are for the PI reviewing what happened. The decision is [ADR-25](../../adr/25-session-logging-two-logs.md).

---

## Multi-machine safety

Per-session files are named by `YYYY-MM-DD-HHMM`, so files from different machines don't collide during sync. Each machine writes its own session files; the vault accumulates them from all machines without conflict.

---

## Related

- The Linter engine (owns `system/logs/` and rotates the audit log): [Engines](../engines/README.md)
- Session-log granularity (per-session files, not per-action): [Memory substrates](../../reference/memory.md)
- Audit log (the other log): [Policy MCP](../../reference/policy-mcp.md)
