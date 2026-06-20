---
topic: decisions
id: 83
title: Direct PI relate control
status: accepted
date_proposed: 2026-06-19
date_resolved: 2026-06-19
assumes: [52, 71, 72, 79, 81]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
---

# ADR-83: Direct PI relate control

## Context

ADR-52 makes `links:` the authored connection layer: agents may propose typed
links, but the PI confirms them. In the current interface, that confirmation is
still too close to raw YAML: the PI either hand-edits `links:` frontmatter or
accepts an agent proposal through ordinary note editing. The alpha.7 gate
dashboard work kept this gap explicit rather than smuggling in a half-designed
edge editor. The missing surface is not a new graph model; it is a safer,
faster way for the PI to write the existing source-of-truth field.

## Decision

Memoria will provide a **direct PI relate control**: an Obsidian command or
form-driven action that lets the PI choose a source note, a relation type, and a
target note, preview the resulting frontmatter change, and apply it to the
source note's existing `links:` map.

The control is a convenience writer over the current contract, not a new source
of truth. It writes only schema-valid `links:` entries, preserves existing
frontmatter, and relies on the Linter/pre-commit checks for integrity. It does
not write Catalog `relationships`, does not create hidden sidecar edge records,
does not infer relations autonomously, and does not expand the relation
vocabulary without a separate schema/reference change.

## Consequences

- The PI gets a low-friction way to connect claims, sources, hubs, and thesis
  notes without remembering YAML shape.
- `links:` remains the only durable authored-edge record, so Bases, dashboards,
  cluster views, and argument-graph operations keep reading the same field.
- Agent-proposed links stay proposals. The relate control can be the acceptance
  surface for a proposed edge, but it must make the PI's confirmation explicit.
- Validation remains structural: the control prevents malformed writes where it
  can, while the Linter remains authoritative for unresolved wikilinks, wrong
  endpoint categories, and schema drift.
- Future relation-vocabulary changes, automated relation suggestions, or
  generated Canvas/projector edges require their own decision/update; they are
  not bundled into this UI control.

## When this matters

Schedule this when hand-editing `links:` becomes a recurring synthesis
bottleneck, when project argument work needs faster support/contradiction entry,
or when agent-proposed relation cards need a dedicated acceptance surface. It
also becomes higher priority if first-run feedback shows that the Knowledge gate
looks complete but users cannot tell how to integrate a claim into the graph.

## Alternatives considered

**Keep hand-editing `links:` only.** This preserves the cleanest architecture,
but makes the most important graph operation depend on frontmatter fluency. That
is tolerable during early alpha work and poor as soon as the vault has enough
claims for relation work to become routine.

**Create standalone edge notes or a sidecar edge store.** Rejected because it
splits the authored-edge source of truth. The existing `links:` map is already
linted, queryable, and consumed by dashboards and graph operations.

**Use Canvas as the edge editor.** Rejected for this decision because Canvas is
a spatial view, not the authoritative record. A future projected Canvas may
visualize or propose edges, but confirmed edges still land in `links:`.

**Let agents write confirmed relations directly.** Rejected because relation
choice is PI judgment under ADR-52. Agents can propose candidates and rationale;
the control is the human confirmation surface.

## Related

- **Workflows affected:** Knowledge synthesis, claim linking, Project argument
  graph work, and agent-proposed relation review.
- **Files affected:** `src/system/scripts/`, `src/.obsidian/plugins/quickadd/data.json`,
  `src/.obsidian/plugins/cmdr/data.json`, `src/spaces/knowledge.md`, `docs/reference/linking.md`,
  `docs/reference/frontmatter.md`, and the claim-linking how-to.
- **Related decisions / Depends on:** [ADR-52](52-links-vs-relationships.md),
  [ADR-71](71-structured-capture-forms.md),
  [ADR-72](72-command-surfacing.md),
  [ADR-79](79-argument-graph-and-warrant.md),
  [ADR-81](81-persistent-gate-dashboards.md).
- **Source discussion:** implementation tracker
  [#691](https://github.com/eranroseman/memoria-vault/issues/691).
