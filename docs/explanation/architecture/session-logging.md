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

## Two logs

The audit log and per-request summaries are different artifacts written for
different readers. The audit log records gated writes for forensic review. The
per-request summaries digest what a request accomplished so the PI can inspect a
session without reading the whole audit trail.

The exact paths, writers, and retention contract belong in [Memory
substrates](../../reference/memory-substrates.md) and [Policy audit
log](../../reference/policy-audit-log.md).

---

## Why the two-log separation

The audit log answers "did this write happen and was it authorized?" — it is
forensic and append-only. Because each write is hash-paired (the mechanism is
owned by [Policy audit log](../../reference/policy-audit-log.md)), a write can be reversed
and an edit made outside the trail is detectable; the Linter closes the loop over
this log with its `audit-unpaired-writes` and `vault-hash-drift` detectors (a
legitimate human edit in an optional editor can surface on the latter too, by
design — see [Operations](../execution/operations.md)). Per-request summaries answer "what
did the request accomplish?" — they are per-request digests.

Combining them would make the audit log verbose (request detail) and would make
request summaries harder to query (mixed with per-write events). Each log has a
different reader: the audit log feeds dashboards and tamper detection; request
summaries are for the PI reviewing what happened. The decision is
[quarantine-and-verify with durable, audit-logged crash recovery](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md).

---

## Multi-machine safety

Per-request files are named by `YYYY-MM-DD-HHMM`, so files from different
machines don't collide during sync. Each machine writes its own summary files;
the workspace accumulates them from all machines without conflict.

---

## Related

- The Linter operation (reads `system/logs/`; runs the integrity checks; writes the request digests): [Operations](../execution/operations.md)
- Session-log granularity (per-request files, not per-action): [Memory substrates](../../reference/memory-substrates.md)
- Audit log (the other log): [Policy gate](../../reference/policy-mcp.md)
