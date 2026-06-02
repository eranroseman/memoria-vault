---
title: Session logging
parent: Architecture
---

# Session logging

Session logging is a system mechanism, not a workflow. Every agent session produces a per-session log that Git preserves — there is no card, nothing to claim, and no state transition. It runs underneath the card-driven workflows rather than being one of them.

---

## Two logs in `99-system/logs/`

These are different artifacts written by different components with different lifecycles. Don't conflate them.

| Log | Path | Writer | Lifecycle |
| --- | --- | --- | --- |
| **Per-session summaries** | `99-system/logs/sessions/YYYY-MM-DD-HHMM.jsonl` | Linter (summarizes Hermes raw activity) | One file per session; never rotated; accumulate indefinitely |
| **Policy MCP audit log** | `99-system/logs/audit.jsonl` | Policy MCP | Append-only; rotated weekly by the Linter |

The audit log is what the [audit-log dashboard](../dashboards/) and [fleet-health dashboard](../dashboards/) read. The per-session summaries are the narrative record of what happened in a session — which skills ran, what decisions were made, which cards were advanced.

---

## Why the two-log separation

The audit log answers "did this write happen and was it authorized?" — it is forensic, append-only, and hash-chained. Per-session summaries answer "what did the session accomplish?" — they are narrative, per-session, and not hash-chained.

Combining them would make the audit log verbose (session narrative) and would make session summaries harder to query (mixed with per-write events). Each log has a different reader: the audit log feeds dashboards and tamper detection; session summaries are for the human reviewing what happened.

---

## Why the sessions directory is not pre-created

The `99-system/logs/sessions/` directory is not pre-created in the starter vault. This is an intentional omission — including the directory in the vault repository would populate it with an empty tracked folder, which creates noise in git history as session files accumulate. The installer creates the directory on first setup. If the directory is missing, session logging silently fails; the setup guide at [How to set up the vault](../../how-to-guides/setup/set-up-the-vault.md) covers this.

---

## Multi-machine safety

Per-session files are named by `YYYY-MM-DD-HHMM`, so files from different machines don't collide during sync. Each machine writes its own session files; the vault accumulates them from all machines without conflict.

---

## Related

- Linter (owns `99-system/logs/` and rotates the audit log): [The Linter](../profiles/linter.md)
- Session-log granularity (per-session files, not per-action): [Memory substrates](../../reference/memory.md)
- Audit log (the other log): [Policy MCP](../../reference/policy-mcp.md)
