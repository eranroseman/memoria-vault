---
topic: decisions
id: 18
title: Evidence quality fields layer
status: proposed
date_proposed: 2026-05-15
date_resolved:
supersedes: []
superseded_by: []
---

# ADR-18: Evidence quality fields layer

## Context

Adding `funding`, `coi` (conflict of interest), `risk_of_bias`, `population`, `intervention_type` fields to paper-notes supports systematic-review work. Empirical studies need these for transparency; theoretical and technical work doesn't.

## Decision

**Adopt only when a project protocol or target journal requires it.** Apply only to empirical papers (RCT, controlled-experiment, quasi-experimental, observational, mixed-methods); set `risk_of_bias: NA` for theoretical and technical work. Per-project activation, not baseline schema.

## Consequences

- Theoretical and technical papers stay clean — only empirical work carries the quality fields.
- When a protocol or target journal demands them, the fields are already specified and ready to populate.
- The `NA` convention for non-empirical work means the fields can coexist with theoretical sources without polluting queries.

## Alternatives considered

**Always-on schema**: See [adopt-on-demand cluster rationale](adopt-on-demand-for-reviews.md).

**Per-project schema branch** (a fork of the paper-note template): rejected — additive fields are cheaper than maintaining two templates.

## Related

- **Part of:** [Adopt-on-demand: systematic-review tooling](adopt-on-demand-for-reviews.md) — the shared rationale, plus the other three members (ADR-12, ADR-19, ADR-20).
- **Files affected:** `00-meta/03-templates/paper-note.md` (in the starter vault), [vault/README.md](../../explanation/vault/README.md)
