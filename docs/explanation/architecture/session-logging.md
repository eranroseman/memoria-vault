---
title: Session logging
parent: Architecture
grand_parent: Explanation
nav_order: 4
---

# Session logging

Session logging is a system mechanism, not a workflow. The policy gate records
every gated write to an audit log that Git preserves — there is no card, nothing
to claim, and no state transition. It runs underneath request-driven workflows
rather than being one of them.

A second, per-request log — a deterministic digest the Linter writes from the
audit trail — accumulates alongside it under `system/logs/sessions/`. This page
explains the two-log design and why they stay separate.

---

## Two logs in `system/logs/`

These are different artifacts written by different components with different lifecycles. Don't conflate them.

| Log | Path | Writer | Lifecycle |
| --- | --- | --- | --- |
| **Policy gate audit log** | `system/logs/audit.jsonl` | Policy gate | Append-only **forever** — never rotated ([ADR-127](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)); growth is surfaced by the Linter's `audit-log-size` advisory (50 MB) |
| **Per-request summaries** | `system/logs/sessions/YYYY-MM-DD-HHMM.jsonl` | Linter (`runtime/subsystems/integrity/linter/session_summary.py`, scheduled integrity run) | One file per request; never rotated; accumulate indefinitely |

The audit log is what the audit-log
[dashboard](../dashboards/README.md) reads. The per-request summaries are
**deterministic digests** of what happened in a session — the Linter is zero-LLM,
so the digest is derived from the audit trail, not narrated: a header (request,
actor, start/end, counts by action and decision) plus one record per
touched path (actions, final decision, final `after_hash`). The writer is
idempotent (a digested request is never rewritten) and only digests requests
quiet for 24 h, so in-flight requests are never summarized early.

---

## Why the two-log separation

The audit log answers "did this write happen and was it authorized?" — it is
forensic and append-only. Because each write is hash-paired (the mechanism is
owned by [Policy gate](../../reference/policy-mcp.md)), a write can be reversed
and an edit made outside the trail is detectable; the Linter closes the loop over
this log with its `audit-unpaired-writes` and `vault-hash-drift` detectors (a
legitimate human edit in an optional editor can surface on the latter too, by
design — see [Operations](../operations.md)). Per-request summaries answer "what
did the request accomplish?" — they are per-request digests.

Combining them would make the audit log verbose (request detail) and would make
request summaries harder to query (mixed with per-write events). Each log has a
different reader: the audit log feeds dashboards and tamper detection; request
summaries are for the PI reviewing what happened. The decision is
[ADR-127](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md).

---

## Multi-machine safety

Per-request files are named by `YYYY-MM-DD-HHMM`, so files from different
machines don't collide during sync. Each machine writes its own summary files;
the workspace accumulates them from all machines without conflict.

---

## Related

- The Linter operation (reads `system/logs/`; runs the integrity checks; writes the request digests): [Operations](../operations.md)
- Session-log granularity (per-request files, not per-action): [Memory substrates](../../reference/memory-substrates.md)
- Audit log (the other log): [Policy gate](../../reference/policy-mcp.md)
