---
topic: decisions
id: 100
title: Exploration-trace capture
status: accepted
date_proposed: 2026-06-19
date_resolved: 2026-06-19
assumes: [30, 52]
supersedes: [65]
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 100
---

# ADR-100: Exploration-trace capture

## Context

Map and scope work often explores directions that turn out not to help. Without a
trace, the human may repeat the same dead end later. But rejected directions are
project-local context, not canonical knowledge.

## Decision

Memoria captures rejected directions and dead ends as a structured artifact
beside a Librarian map-lane scope or gap report. The artifact stays at the project
level and is never auto-promoted into canonical knowledge layers.

## Consequences

- Reduces repeated exploration of known dead ends.
- Adds an artifact-management obligation to map-lane outputs.
- Risks over-recording if every weak lead becomes durable state.

## When this matters

The human notices repeating an already-explored direction: the "I am sure I
checked this before" failure mode.

## Alternatives considered

**Do not record rejected directions.** Simpler, but repeats wasted exploration.

**Promote traces to canonical knowledge.** Rejected because dead ends are often
project-local and may be productive elsewhere.

## Related

- **Supersedes:** [ADR-65](65-retrieval-and-schema-extensions.md).
- **Related decisions / Depends on:** [ADR-30](30-deterministic-ingest-pipeline.md), [ADR-52](52-links-vs-relationships.md).
- **Tracking issue:** [#713](https://github.com/eranroseman/memoria-vault/issues/713).
