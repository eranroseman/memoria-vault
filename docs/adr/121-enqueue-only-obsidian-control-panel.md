---
topic: decisions
id: 121
title: Obsidian control panel mutates only by enqueueing worker jobs
nav_exclude: true
status: accepted
date_proposed: 2026-06-29
date_resolved: 2026-06-29
assumes: [28, 74]
supersedes: []
superseded_by: []
---

# ADR-121: Obsidian control panel mutates only by enqueueing worker jobs

## Context

The first Inspector design made the Memoria Inspector read-only to avoid creating a
second write surface. alpha.11 changes the storage model: machine writes and promotions
must route through the worker/trusted-writer boundary, while the Obsidian plugin becomes
the PI's control panel for inspection, integrity actions, and later trace operations.

The read-only-only rule is now too narrow, but the safety reason behind it still holds.

## Decision

The Memoria Obsidian control panel may mutate only by enqueueing worker jobs under
`.memoria/queue/pending/`. It never writes Concepts, journal files, generated projections, or
`check_status` directly.

The worker owns execution and journal/audit coupling. The plugin owns only a small enqueue
request shape: `kind: operation`, `operation_id`, `payload`, `status: pending`, and metadata.

For checked Concept promotion, the worker/trusted-writer path also owns the operation
`required_checks` gate. alpha.11 supports the `memoria-profile` pre-promotion check and fails
closed on empty or unsupported promotion-check lists before marking a Concept `checked`.

## Consequences

- The PI gets an in-Obsidian action surface without bypassing the alpha.11 writer boundary.
- Static tests can prove the plugin has no direct canonical write path.
- Worker tests must cover every operation id the plugin can enqueue.
- The old Inspector read-only guarantee is replaced by a narrower and enforceable guarantee:
  read generated status freely; mutate only by queueing work for the worker.

## Alternatives considered

**Keep the Inspector read-only and put controls in QuickAdd.** Rejected: it splits the
alpha.11 integrity workflow across an observation pane and unrelated palette actions.

**Let the plugin call Local REST or edit Concepts directly.** Rejected: it bypasses the
worker/trusted-writer trace boundary and recreates the policy complexity the read-only
Inspector design avoided.

**Adopt an external admin GUI.** Rejected because a broad GUI over files, terminal,
memory, and sessions would add another write-capable surface outside the vault's
policy-gated flows. The durable need is in-Obsidian forensic visibility plus explicit
queued operations.

## Related

- **Depends on:** [ADR-28](28-write-gate-as-plugin.md), [ADR-74](74-pinned-obsidian-plugin-supply-chain.md)
- **Implementation:** `vault-template/.obsidian/plugins/memoria-inspector/`,
  `src/memoria_vault/runtime/worker.py`,
  `src/memoria_vault/runtime/trusted_writer.py`
- **Checks:** `tests/test_memoria_inspector.py`, `tests/test_worker_queue.py`,
  `tests/test_trusted_writer.py`, `tests/test_operations.py`, `scripts/plugin_provenance_doctor.py`
