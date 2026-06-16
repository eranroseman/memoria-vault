---
topic: decisions
id: 79
title: Argument graph and warrant
status: accepted
date_proposed: 2026-06-16
date_resolved: 2026-06-16
assumes: [8, 52, 77, 78]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 79
---

# ADR-79: Argument graph and warrant

## Context

The Project gate needs to produce an argument, not just organize a cluster of
notes. The existing descriptive knowledge map shows what exists inside a project
scope; it does not say how a thesis is defended. The missing layer is the
thesis-rooted argument graph: the typed relation subgraph that connects evidence,
reasons, objections, and rebuttals to the thesis.

## Decision

Memoria treats the **argument graph** as the `supports` / `contradicts` subgraph
rooted at a thesis. Project impact, gap ranking, saturation, and outline
structure derive from this graph, not from the descriptive topology alone.

`warrant` becomes an optional attribute on a relation: the inferential rule that
explains why one note supports or contradicts another. It is free to populate
when known, but its absence is not a blocker in the alpha.5 cut. The
unstated-warrant gap detector remains off until relation coverage and PI demand
justify it; this ADR only reserves the shape.

Structural Operations may test presence and topology: relation type, path to the
thesis, addressed refutations, graph maturity, and whether a warrant field is
present. They may not judge whether a warrant is good, whether the strongest
counterargument was chosen, or whether the thesis is true. Those are PI judgment
or gated proposal territory.

## Consequences

- Outlines are defenses of a thesis, not ordered copies of a map. First-level
  reasons become section structure; contradicting paths become counterargument
  work.
- Gap impact is thesis-relative. A source or knowledge gap off the argument path
  can be interesting while having impact zero for this project.
- `warrant` can be added without blocking existing relations or requiring a
  mass backfill.
- The graph maturity default requires at least one addressed support and one
  addressed contradiction so the Project gate does not report saturation over a
  one-sided graph.

## Alternatives considered

**Use only the descriptive map.** Rejected: map topology can produce a survey,
but it cannot distinguish a defended argument from an organized literature area.

**Make `warrant` mandatory.** Rejected: it would make relation entry too heavy
and punish already useful support/contradiction links.

**Enable unstated-warrant gaps immediately.** Rejected: absence detection is
cheap, but it is also gameable and noisy before the relation layer has enough
coverage.

## Related

- **Files affected:** relation schema/contracts, Project structural-impact
  Operation, Project dashboards.
- **Related decisions / Depends on:** [ADR-08](08-typed-relations-frontmatter.md),
  [ADR-52](52-links-vs-relationships.md),
  [ADR-77](77-project-gate.md),
  [ADR-78](78-thesis-note-type.md).
- **Source discussion:** [alpha.5 project-starter](../releasing/0.1.0-alpha.5/tmp/project-starter.md),
  [#579](https://github.com/eranroseman/memoria-vault/issues/579).
