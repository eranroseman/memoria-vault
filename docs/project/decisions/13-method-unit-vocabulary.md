---
topic: decisions
id: 13
title: Method-unit vocabulary
status: retired
date_proposed: 2026-05-15
date_resolved: 2026-05-27
supersedes: []
superseded_by: []
---

# ADR-13: Method-unit vocabulary

## Context

Original question: tag claim notes with methodological patterns (Idea2Story-style — pipeline that chains from raw idea through claim extraction to story assembly — e.g., `methods-units: [micro-randomized-trial, EMA]`) to enable methodological querying?

## Decision

**Retired.** Premature ontology risk. The original recommendation was "start with free-text `methods:` and crystallize a vocabulary only when patterns recur" — but no triggering pattern has emerged, and the deferral has no defined adoption signal. Retire this decision; revisit only if a concrete recurring methodological query that needs structured tags shows up in practice.

## Consequences

- `methods:` stays free-text indefinitely.
- Methodological querying remains imprecise (tag-search, no structured aggregation).
- The retirement preserves the rationale: don't build vocabularies that can't yet be named.

## Alternatives considered

**Keep as proposed-deferred**: rejected — a deferral with no trigger isn't a decision, it's a parking spot. Better to retire and re-propose under a new ADR if and when a real need surfaces.

## Related

- **Files affected:** [vault/README.md](../../explanation/vault/README.md), [vault/frontmatter-schema.md](../../reference/frontmatter-schema.md)
