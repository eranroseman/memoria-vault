---
topic: decisions
id: 122
title: SQLite working state is a cache behind the checked Concept boundary
nav_exclude: true
status: accepted
date_proposed: 2026-06-30
date_resolved: 2026-06-30
assumes: [28, 55, 121]
supersedes: []
superseded_by: []
---

# ADR-122: SQLite working state is a cache behind the checked Concept boundary

## Context

Alpha.12 adds durable worker state for request envelopes, materialization recovery,
catalog rows, and journal indexing. The earlier file-only path kept Git as the only
durable surface, but it could not represent a queued request without a fragile JSON
mirror, replay a checked file from a stored payload, or render `references.bib` from
one checked catalog table.

## Decision

Memoria stores runtime working state in `.memoria/state/memoria.sqlite`, with the
worker still owning canonical writes through the trusted-writer path. The SQLite DB
records request envelopes, append-only hash-chained journal rows, catalog source rows,
file output state, materialization payloads, and derivation links.

The DB is not a second live Concept store. A file-backed Concept becomes consumable
only after it is both `checked` and materialized; checked Concepts and tracked
projections remain the PI-facing vault surface. `.memoria/queue/` stays as an
Obsidian-compatible mirror for pending/running/done/failed jobs, not the state owner.

## Consequences

- Worker jobs can recover from missing queue mirror files because the request envelope
  lives in SQLite.
- Checked machine outputs have durable payloads for replay, with hash mismatch or
  missing payload failures recorded fail-closed.
- `references.bib` renders from checked SQLite catalog rows, with checked source
  Concepts as a fallback only when no catalog rows exist.
- Git remains the reviewable record for Concepts, projections, and JSONL journals;
  SQLite supports operations and recovery behind that surface.
- Integrity checks must protect citation survival so notes, digests, and hubs remain
  meaningful when read without SQLite.

## Alternatives considered

**Keep JSON queue files as the source of truth.** Rejected because file mirrors are easy
to delete or strand mid-transition, and the worker needs idempotency, causal refs, and
schedule metadata in one durable envelope.

**Promote SQLite to the canonical Concept store.** Rejected because it would make the
PI-facing knowledge corpus opaque to Obsidian, Git diffs, and the existing checked
Concept schema/linter boundary.

**Store everything as Git-tracked JSONL.** Rejected because recovery queries,
idempotency lookups, and materialization replay need indexed state, while Git-tracked
JSONL remains the audit and replay projection.

## Related

- **Depends on:** [ADR-28](28-write-gate-as-plugin.md),
  [ADR-55](55-src-scaffold-populate-golden-copy.md),
  [ADR-121](121-enqueue-only-obsidian-control-panel.md)
- **Implementation:** `src/memoria_vault/runtime/state.py`,
  `src/memoria_vault/runtime/worker.py`,
  `src/memoria_vault/runtime/trusted_writer.py`,
  `src/memoria_vault/runtime/capture.py`
- **Checks:** `tests/test_alpha12_state.py`, `tests/test_worker_queue.py`,
  `tests/test_capture.py`, `tests/test_integrity.py`
- **Source discussion:** [PR #1032](https://github.com/eranroseman/memoria-vault/pull/1032)
