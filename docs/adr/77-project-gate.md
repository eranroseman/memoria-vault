---
topic: decisions
id: 77
title: Project gate
nav_exclude: true
status: accepted
date_proposed: 2026-06-16
date_resolved: 2026-06-16
assumes: [48, 54, 69, 119]
supersedes: []
superseded_by: []
---

# ADR-77: Project gate

## Context

The existing workspace shell left Project work mostly empty while Studio carried
drafting. alpha.5 is the first checkpoint where that surface has a concrete job:
bounded inquiry that turns catalog/source work into a
defended or falsified thesis. The gate must preserve Memoria's deepest boundary:
agents propose, deterministic Operations derive views, and the PI promotes.

## Decision

Memoria adopts a **Project gate** for bounded research inquiry. A project is rooted
in a `project` Concept under `knowledge/projects/`; its optional `thesis` field
points at the checked `note` being defended or falsified. The gate
surfaces the project question, thesis, descriptive map, argument graph, ranked
gaps, saturation signal, and outline path from Obsidian, using the existing
workspace machinery and a custom Bases view where the Obsidian API permits it.

All load-bearing Project logic is deterministic: map traversal, structural
impact, graph maturity, saturation, and index-note materialization are Operations
over vault state. Agents may discover sources, propose gaps, and draft outlines,
but the gate never asks an LLM to judge truth, infer maturity, or promote a
thesis. The PI remains the author of the question and thesis and the only actor
who can promote the thesis note to `checked`.

The conservative graph-maturity default is a connected thesis-rooted component
with at least five addressed relations, including at least one `supports` edge
and at least one `contradicts` edge. The default materialization shape is a
single generated project index note read by the custom Bases view; per-note
stamps are reserved for cases where a later implementation cannot use the view.

> **Implementation status (2026-06-21).** The deterministic gate logic ships in
> Operations: thesis-rooted traversal, structural impact, maturity thresholds,
> saturation, and index-note materialization are implemented and tested. The custom
> `registerBasesView` surface remains the experimental part; the shipped Obsidian
> surface is the `.base` dashboard plus Markdown project index notes.

## Consequences

- Project becomes a first-class work surface rather than a promise hidden behind
  Studio.
- The gate can argue for stopping when the argument is saturated, but only over
  relations the PI or gated proposals have actually supplied. Determinism makes
  the computation repeatable, not the conclusion true.
- Falsifying a thesis is a finished project result: the project points to the checked
  note and preserves the argument subgraph that refuted it rather than treating the
  outcome as failure.
- The implementation sequence is structural-first: schemas and templates, then
  graph/impact Operations, then gap/saturation logic, then the Obsidian surface.
- The custom Bases view remains a version-pinned pilot because `registerBasesView`
  exists in the published Obsidian API but remains a narrower extension surface
  than ordinary Markdown dashboards.

## Alternatives considered

**Keep Project as Studio-only drafting.** Rejected: Studio answers "what am I
writing?", while Project answers "what bounded inquiry am I driving to an
answer?" Merging them keeps the missing middle between map and outline.

**Use agent judgment for maturity and saturation.** Rejected: it would turn a
navigation gate into a hidden inference layer. The gate's value is that its logic
is inspectable and repeatable even when the graph inputs are incomplete.

**Materialize derived state onto every note by default.** Rejected: it creates
write amplification and stale frontmatter risk. A generated project index is the
default; per-note stamps need a specific rendering constraint to justify them.

## Related

- **Files affected:** `vault-template/knowledge/projects/`, `vault-template/system/templates/`,
  `vault-template/.memoria/schemas/types/`, `vault-template/.memoria/operations/`, workspace/dashboard
  files.
- **Related decisions / Depends on:** [ADR-54](54-two-decision-kinds-batch-worklists.md),
  [ADR-79](79-argument-graph-and-warrant.md),
  [ADR-119](119-schema-driven-document-creation.md).
- **Source discussion:** alpha.5 workstream
  [#577](https://github.com/eranroseman/memoria-vault/issues/577), spike workstream
  [#576](https://github.com/eranroseman/memoria-vault/issues/576), and merged implementation
  PRs [#603](https://github.com/eranroseman/memoria-vault/pull/603),
  [#604](https://github.com/eranroseman/memoria-vault/pull/604),
  [#605](https://github.com/eranroseman/memoria-vault/pull/605),
  [#606](https://github.com/eranroseman/memoria-vault/pull/606),
  [#607](https://github.com/eranroseman/memoria-vault/pull/607).
