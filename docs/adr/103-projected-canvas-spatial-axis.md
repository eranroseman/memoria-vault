---
topic: decisions
id: 103
title: Projected Canvas spatial axis
nav_exclude: true
status: rejected
date_proposed: 2026-06-19
date_resolved: 2026-07-02
assumes: [52, 79, 83, 102, 116]
supersedes: []
superseded_by: []
---

# ADR-103: Projected Canvas spatial axis

> **Status note (0.1.0-alpha.15):** rejected: spatial canvas is not the validated default; tabular/faceted views remain the baseline.

## Context

ADR-79 gives Project work an argument-graph vocabulary, but the current shipped UI
is intentionally tabular: Spaces and Bases carry the day-to-day workflow. Canvas
could help when arrangement and edges are the content, but Canvas JSON is invisible
to the Linter, Bases, and graph operations. Treating hand-drawn Canvas edges as
truth would repeat the off-store failure that the Concept schema boundary rejects.

## Proposal

Memoria may add Canvas as a **spatial projection**, not as an authoritative edge
store. Confirmed edges stay in `links:` frontmatter. A projected Canvas renders
file-reference nodes and relation-labelled edges from those authored links; a
scratch Canvas remains a human sense-making workspace whose edges become durable
only when the PI graduates them through the direct relate control or another
`links:` writer.

The projected Canvas contract is:

- nodes point to real notes rather than copied text;
- edges derive from `links:` and optional ADR-79 warrants;
- Project pages open projected canvases by link/button in their own pane, not as a
  load-bearing inline embed;
- inline embeds may be thumbnails only, because they show topology but not file-node
  content;
- projected canvases are read-only/regenerated and offer a fork-to-scratch escape;
- accepting the ephemeral-position model requires a layout-feasibility spike that
  proves incremental-stable layout: existing nodes keep position and new nodes are
  placed without global reflow;
- if that spike fails, persisted positions in a governed projection registry are
  the designed fallback. Authoritative hand-drawn Canvas edges remain rejected.

## Consequences

- The spatial surface can support argument maps without splitting the edge source of
  truth.
- The PI gets an escape hatch for exploratory arrangement while durable relations
  still land in `links:`.
- The hardest technical requirement is layout stability, not Canvas file creation.
  Without it, regenerated views erase the PI's mental map.
- Forked scratch canvases need a staleness signal showing how many source-graph
  edges changed since the fork.

## When this matters

This becomes worth deciding when real Project work shows that tabular Spaces and
Bases cannot carry the argument; when the PI asks for a spatial map while reviewing
claims/theses; or when relation density makes the graph's topology itself the
object under discussion.

## Alternatives considered

**Use authored Canvas as the edge source of truth.** Rejected because it bypasses
the Linter, frontmatter schemas, and ADR-79 graph operations.

**Use projected Canvas with no layout persistence.** Plausible only if the layout
spike proves stable enough. Otherwise every regeneration resets the user's mental
map.

**Skip Canvas and keep tables only.** Correct for the current sparse vault and
therefore the shipped posture. It may become too narrow for dense argument review.

## Related

- **Workflows affected:** Project argument review, Knowledge synthesis, scratch
  spatial sense-making, and direct relation authoring.
- **Files affected:** future projection engine/registry, `projects/` pages,
  Canvas projection tests, and relation-authoring docs.
- **Related decisions / Depends on:** [ADR-52](52-links-vs-relationships.md),
  [ADR-79](79-argument-graph-and-warrant.md),
  [ADR-83](83-direct-pi-relate-control.md),
  [ADR-102](102-disposable-projection-engine.md),
  [ADR-116](116-obsidian-surface-architecture.md).
- **Tracking issue:** [#721](https://github.com/eranroseman/memoria-vault/issues/721).
