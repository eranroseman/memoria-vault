---
topic: decisions
id: 99
title: MASSW-aligned paper aspects
nav_exclude: true
status: proposed
date_proposed: 2026-06-19
date_resolved:
assumes: [30]
supersedes: []
superseded_by: []
---

# ADR-99: MASSW-aligned paper aspects

## Context

Paper summaries do not always expose method or outcome in a queryable way.
MASSW-style aspects could make key idea, method, and outcome queryable, but they
add an extraction call and risk low-quality abstract-only fields.

## Proposal

Memoria may add `_aspects.key_idea`, `_aspects.method`, and `_aspects.outcome` to
paper records, populated at ingest, human-correctable at review, and queryable in
Obsidian. `context` and `projected_impact` are excluded because they overlap other
fields or need evidence ingest lacks.

## Consequences

- Improves filtering by method and outcome.
- Adds extraction cost and review burden per paper.
- Abstract-only aspects may be weaker than full-text or figure-informed aspects.

## When this matters

The Librarian regularly ingests papers and the human wants to filter by method or
outcome, but must read full summaries to do it.

## Alternatives considered

**Adopt all MASSW fields.** Rejected because `context` overlaps existing metadata
and `projected_impact` needs post-publication evidence.

**Wait for figure-informed extraction.** Rejected as a prerequisite because an
abstract-only slice can be useful independently.

## Related

- **Related decisions / Depends on:** [ADR-30](30-deterministic-ingest-pipeline.md).
- **Tracking issue:** [#712](https://github.com/eranroseman/memoria-vault/issues/712).
