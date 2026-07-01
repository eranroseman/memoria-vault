---
topic: decisions
id: 122
title: SQLite working state and catalog records sit behind the checked Concept boundary
nav_exclude: true
status: accepted
date_proposed: 2026-06-30
date_resolved: 2026-06-30
assumes: [28, 55, 119]
supersedes: [49, 121]
superseded_by: []
---

# ADR-122: SQLite working state and catalog records sit behind the checked Concept boundary

## Context

Alpha.12 adds durable worker state for request envelopes, materialization recovery,
catalog rows, and journal indexing. The earlier file-only path kept Git as the only
durable surface, but it could not represent a queued request without a fragile JSON
mirror, replay a checked file from a stored payload, or render `references.bib` from
one checked catalog table.

[ADR-49](49-catalog-in-bases-linter-monitor.md) made markdown records under
`catalog/` the catalog source of truth so Obsidian Bases could render them. That
model is now too strong: the worker needs indexed catalog rows for materialization,
idempotency, bibliography rendering, and later provider provenance, while Bases are
only a view layer.

## Decision

Memoria stores runtime working state and catalog record state in
`.memoria/state/memoria.sqlite`, with the worker still owning canonical writes through
the trusted-writer path. The SQLite DB records request envelopes, append-only
hash-chained journal rows, catalog source rows, file output state, materialization
payloads, and derivation links.

The DB is not a second live Concept store. File-backed Concepts become consumable only
after they are both `checked` and materialized; checked Concepts and tracked projections
remain the PI-facing vault surface. Catalog rows are records behind that surface:
`references.bib`, digests, source citations, and any catalog UI read from them, but
markdown catalog frontmatter does not overrule them.

PI and operator mutation follows the CLI request path: commands insert SQLite
request envelopes, the worker claims pending requests from SQLite, and every
mutation still passes through the trusted-writer/check boundary. The Memoria
Inspector remains read-only and may not write catalog rows, Concepts, journal
files, projections, `check_status`, SQLite requests, or queue files. There is no
`.memoria/queue/` mirror; SQLite request state is the worker authority.

## Consequences

- Worker jobs recover from SQLite request state; there are no queue mirror files
  to recover from or keep in sync.
- Checked machine outputs have durable payloads for replay, with hash mismatch or
  missing payload failures recorded fail-closed.
- `references.bib` renders from checked SQLite catalog rows, with checked source
  Concepts as a fallback only when no catalog rows exist.
- [ADR-49](49-catalog-in-bases-linter-monitor.md)'s catalog-frontmatter source-of-truth
  decision is superseded. Bases may still render catalog-shaped views while those
  files exist, but they are projections/fallbacks, not the catalog authority.
- Git remains the reviewable record for Concepts, projections, and JSONL journals;
  SQLite supports operations and recovery behind that surface.
- Integrity checks must protect citation survival so notes, digests, and hubs remain
  meaningful when read without SQLite.

## Alternatives considered

**Keep JSON queue files as the source of truth.** Rejected because file mirrors are easy
to delete or strand mid-transition, and the worker needs idempotency, causal refs, and
schedule metadata in one durable envelope.

**Keep catalog markdown records as the source of truth.** Rejected because it makes
bibliography rendering, provider provenance, idempotent enrichment, and materialization
recovery depend on a file shape optimized for Obsidian views rather than worker state.

**Promote SQLite to the canonical Concept store.** Rejected because it would make the
PI-facing knowledge corpus opaque to Obsidian, Git diffs, and the existing checked
Concept schema/linter boundary.

**Store everything as Git-tracked JSONL.** Rejected because recovery queries,
idempotency lookups, and materialization replay need indexed state, while Git-tracked
JSONL remains the audit and replay projection.

## Related

- **Supersedes:** [ADR-49](49-catalog-in-bases-linter-monitor.md),
  [ADR-121](121-enqueue-only-obsidian-control-panel.md)
- **Depends on:** [ADR-28](28-write-gate-as-plugin.md),
  [ADR-55](55-src-scaffold-populate-golden-copy.md),
  [ADR-119](119-schema-driven-document-creation.md)
- **Implementation:** `src/memoria_vault/runtime/state.py`,
  `src/memoria_vault/runtime/worker.py`,
  `src/memoria_vault/runtime/trusted_writer.py`,
  `src/memoria_vault/runtime/capture.py`
- **Checks:** `tests/test_alpha12_state.py`, `tests/test_worker_queue.py`,
  `tests/test_capture.py`, `tests/test_integrity.py`
- **Source discussion:** [PR #1032](https://github.com/eranroseman/memoria-vault/pull/1032)
