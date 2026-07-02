---
topic: decisions
id: 102
title: Disposable projection engine
nav_exclude: true
status: superseded
date_proposed: 2026-06-19
date_resolved: 2026-07-02
assumes: [57, 69, 116, 119]
supersedes: []
superseded_by: [130]
---

# ADR-102: Disposable projection engine

> **Status note (0.1.0-alpha.15):** superseded by [ADR-130](130-read-api-surfaces-and-copi.md). Kept for decision history; current architecture is carried by the consolidation ADR.

## Context

Memoria already has one narrow projection: Hermes board state is mirrored into
markdown rows so Obsidian can render it as ordinary vault content. Several future
surfaces want the same pattern for audit windows, metrics, eval runs, skill state,
and other non-markdown sources. Building that as ad hoc emitters would multiply
stale-row, schema-drift, cold-cache, and failure-surfacing bugs.

## Proposal

Memoria may add a deterministic projection engine that renders non-markdown sources
of record into disposable markdown rows under a consumer-only projection zone. The
source remains authoritative; projected files are regenerated, may be deleted on
the next pass, and are never edited by hand.

The contract is strict:

- one source row maps to one projected artifact;
- reconciliation handles create, update, and delete;
- filenames use collision-safe slug/hash encoding while the raw source id remains
  in frontmatter;
- event sources sort on a real event time, while snapshot sources sort on a domain
  key rather than fabricated timestamps;
- output enum values are checked against the same schemas as authored notes;
- dirty source rows are quarantined and logged while conforming rows continue;
- bulk projections wait for Obsidian metadata-cache settlement before signalling
  readiness;
- projector failures raise an Integrity signal and dashboards show a distinct
  "last refresh failed" state.

The projector's operator model is part of this proposal, not an implementation
detail. The engine must name what process runs it, what writes it can perform, how
it coordinates concurrent passes, and how it fits ADR-120/ADR-28's single audited
write path.

## Consequences

- Future non-markdown views share one tested reconciliation and failure model.
- Projected dashboards can stay ordinary Bases/Dataview consumers instead of
  bespoke UI code.
- The system gains a new engine with filesystem write authority; its operator,
  locking, sync, and failure boundaries must be explicit before acceptance.
- Projected artifacts are local runtime products. Multi-device visibility needs
  either local regeneration or a non-git sync story; gitignored projections cannot
  be treated as shared source.

## When this matters

This becomes worth deciding when a real dashboard cannot be expressed as an
authored Base, Dataview over existing logs, or the current board mirror; when stale
projected rows become a recurring release issue; or when telemetry volume makes
pull-on-read views too slow.

## Alternatives considered

**Keep one-off emitters.** Simpler for the first surface, but repeats the hard
parts — deletion, dirty data, schema conformance, cold-cache timing, and failure
states — in every emitter.

**Make projected files authoritative.** Rejected because it creates a second source
of truth. Projections are views; sources of record stay in logs, metrics, board
state, schemas, or authored note frontmatter.

**Do not project; query raw sources directly.** Works for small Dataview or script
readers, but does not give Obsidian Bases a stable one-row-per-object surface and
does not solve operator-facing dashboard ergonomics.

## Related

- **Workflows affected:** Operational-health dashboards, board projection, eval
  trend, skill state, and future integrity projections.
- **Files affected:** future projection engine under `vault-template/.memoria/operations/`,
  projection registry, dashboard references, Linter/projector conformance tests.
- **Related decisions / Depends on:** [ADR-119](119-schema-driven-document-creation.md),
  [ADR-57](57-engines-write-agents-judge.md),
  [ADR-69](69-operations-layer-naming.md),
  [ADR-116](116-obsidian-surface-architecture.md).
- **Tracking issue:** [#719](https://github.com/eranroseman/memoria-vault/issues/719).
