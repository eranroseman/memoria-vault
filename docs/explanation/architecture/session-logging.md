---
title: Session logging
parent: Architecture
grand_parent: Explanation
nav_order: 3
---

# Session logging

Session logging is a system mechanism, not a workflow. Policy-gated adapter
writes produce audit-log evidence; worker requests and trusted-writer commits
also leave SQLite and journal evidence. There is no card, nothing to claim, and
no state transition. Logging runs underneath request-driven workflows rather
than being one of them.

A second, per-request log — a deterministic digest the Linter writes from the
audit trail — accumulates alongside it under `system/logs/sessions/`. This page
explains the two-log design and why they stay separate.

---

## Two logs

The audit log and per-request summaries are different artifacts written for
different readers. The policy audit log records gated adapter writes for
forensic review. Request rows, journal events, and per-request summaries show
what worker-controlled work accomplished so the PI can inspect a session without
reading every event.

These two logs are the **audit** and **analytics** planes of the three planes
described in [Telemetry architecture](telemetry-architecture.md); this page
does not cover the third (diagnostics), which is intentionally out of the
session-inspection surface.

The exact paths, writers, and retention contract belong in [Memory
substrates](../../reference/pipelines-and-io/memory-substrates.md) and [Policy audit
log](../../reference/control-and-policy/policy-audit-log.md).

---

## Why the two-log separation

The policy audit log answers "did this adapter write happen and was it
authorized?" — it is forensic and append-only. Because each policy write is
hash-paired (the mechanism is owned by
[Policy audit log](../../reference/control-and-policy/policy-audit-log.md)), a write can be
reversed and an edit made outside the trail is detectable; the Linter closes the
loop over this evidence with audit and hash-drift detectors. Worker request rows,
journal events, and per-request summaries answer "what did the request
accomplish?" — they are request evidence, not policy-gate evidence.

Combining them would make the audit log verbose (request detail) and would make
request summaries harder to query (mixed with per-write events). Each log has a
different reader: the audit log feeds tamper detection and may feed optional
dashboards; request summaries are for the PI reviewing what happened. The decision is
[quarantine-and-verify with durable, audit-logged crash recovery](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md).

---

## Filename collision safety

Per-request files are named by `YYYY-MM-DD-HHMM`, so repeated operator runs get
stable, sortable names. The supported deployment model remains local-only;
multi-machine sync needs its own deployment decision before support.

---

## Related

- The Linter operation (reads `system/logs/`; runs the integrity checks; writes the request digests): [Operations](../execution/operations.md)
- Session-log granularity (per-request files, not per-action): [Memory substrates](../../reference/pipelines-and-io/memory-substrates.md)
- Audit log (the other log): [Policy gate](../../reference/control-and-policy/policy-mcp.md)
