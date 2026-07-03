---
topic: decisions
id: 94
title: Record linkage for entity deduplication
nav_exclude: true
status: accepted
date_proposed: 2026-06-19
date_resolved: 2026-07-03
assumes: [30, 122]
supersedes: []
superseded_by: []
---

# ADR-94: Record linkage for entity deduplication

## Context

Author and venue entities can duplicate when external IDs are missing or
inconsistent. Memoria already prefers deterministic ingest and catalog integrity;
record linkage should use identifiers and string-similarity blocking before any
LLM judgment.

## Decision

Memoria adds record linkage for entity deduplication through the existing
`check-source-metadata` integrity path. The alpha.15 implementation flags exact
person ORCID/OpenAlex external-ID collisions and exact normalized by-name blocks
from checked graph entities. Findings route to stable unchecked Inbox attention
for human review; the operation never merges identities automatically.

Fuzzy string matching, thresholds, and automatic merge actions stay out until
real corpus misses justify them.

## Consequences

- Reduces duplicate person and venue entities with auditable evidence.
- Requires careful threshold selection to avoid false merges.
- Extends the deterministic ingest discipline without making the LLM an identity
  authority.

## When this matters

Entity notes accumulate duplicate person or venue entries that the human notices
while cleaning the graph.

## Alternatives considered

**Ask the LLM whether two entities match.** Rejected as the primary path because
identity merge needs deterministic evidence and review.

**Only merge on exact external IDs.** Safe, but leaves no-ID duplicates unresolved.

## Related

- **Related decisions / Depends on:** [ADR-30](30-deterministic-ingest-pipeline.md), [ADR-122](122-sqlite-working-state-boundary.md).
- **Tracking issue:** [#707](https://github.com/eranroseman/memoria-vault/issues/707).
