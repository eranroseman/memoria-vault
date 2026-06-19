---
topic: decisions
id: 94
title: Record linkage for entity deduplication
status: proposed
date_proposed: 2026-06-19
date_resolved:
assumes: [30, 49]
supersedes: [59]
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 94
nav_exclude: true
---

# ADR-94: Record linkage for entity deduplication

## Context

Author and venue entities can duplicate when external IDs are missing or
inconsistent. Memoria already prefers deterministic ingest and catalog integrity;
record linkage should use identifiers and string-similarity blocking before any
LLM judgment.

## Proposal

Memoria may add record linkage for entity deduplication: ORCID/OpenAlex IDs first,
then string-similarity blocking over by-name collisions, with human review before
merge when identity is uncertain.

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

- **Supersedes:** [ADR-59](59-classical-method-displacements.md).
- **Related decisions / Depends on:** [ADR-30](30-deterministic-ingest-pipeline.md), [ADR-49](49-catalog-in-bases-linter-monitor.md).
- **Tracking issue:** [#707](https://github.com/eranroseman/memoria-vault/issues/707).
