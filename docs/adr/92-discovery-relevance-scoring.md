---
topic: decisions
id: 92
title: Discovery relevance scoring
status: proposed
date_proposed: 2026-06-19
date_resolved:
assumes: [30]
supersedes: [59]
superseded_by: []
---

# ADR-92: Discovery relevance scoring

## Context

Discovery candidates currently need ranking against the human's research focus.
An LLM skill can rank candidates, but a deterministic scorer could provide an
auditable first ordering using embeddings, citation graph overlap, and topic-tag
overlap.

## Proposal

Memoria may add a deterministic `[!suggestions]` weighted scorer that ranks
discovery candidates against `research-focus.md`, using embedding similarity,
citation-graph overlap, and topic-tag overlap. The scorer would feed triage; it
would not accept or reject candidates automatically.

## Consequences

- Reduces LLM ranking cost and makes the ordering auditable.
- Requires a maintained `research-focus.md` and tuned weights.
- Can become misleading if the focus file drifts from the human's current agenda.

## When this matters

The discovery loop is live and morning triage exceeds 15 minutes because
candidates are not pre-sorted by relevance.

## Alternatives considered

**Keep LLM ranking only.** Flexible, but less reproducible and more expensive.

**Use recency or citation count only.** Cheap, but weakly aligned with the human's
research priorities.

## Related

- **Supersedes:** [ADR-59](59-classical-method-displacements.md).
- **Related decisions / Depends on:** [ADR-30](30-deterministic-ingest-pipeline.md), [ADR-95](95-nightly-proactive-discovery-loop.md).
- **Tracking issue:** [#705](https://github.com/eranroseman/memoria-vault/issues/705).
