---
topic: decisions
id: 98
title: Relation-vocabulary expansion
status: proposed
date_proposed: 2026-06-19
date_resolved:
assumes: [52, 79]
supersedes: [65]
superseded_by: []
---

# ADR-98: Relation-vocabulary expansion

## Context

ADR-52 establishes authored `links:` as the source of truth for typed note
relations. The current vocabulary is intentionally small. Expanding it too early
creates half-populated fields and unreliable queries; expanding it at the right
time can make relation work more expressive.

## Proposal

Memoria may expand the `links:` relation vocabulary one value at a time, starting
with `similar`, then considering `cross-domain` and `uses-method` only after
`similar` proves useful. Relation keys remain documentary and validated for
resolution, not automatically inferred truth.

## Consequences

- Makes graph queries more expressive when the corpus is dense enough.
- Adds template, reference, Linter, and dashboard updates per relation.
- Inconsistent typing makes query results incomplete and erodes trust.

## When this matters

There are at least 200 claim notes and 500 inter-claim wikilinks, and the human
regularly wants "find similar" queries that manual backlink walks do not answer.

## Alternatives considered

**Adopt the full PARNESS taxonomy.** Rejected for now because it was designed for
ML/science workflows and may be wrong-shaped for Memoria's knowledge work.

**Keep only supports/contradicts/extends forever.** Simpler, but likely too narrow
once the claim graph becomes dense.

## Related

- **Supersedes:** [ADR-65](65-retrieval-and-schema-extensions.md).
- **Related decisions / Depends on:** [ADR-52](52-links-vs-relationships.md), [ADR-79](79-argument-graph-and-warrant.md).
- **Tracking issue:** [#711](https://github.com/eranroseman/memoria-vault/issues/711).
