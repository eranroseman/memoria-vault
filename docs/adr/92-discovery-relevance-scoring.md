---
topic: decisions
id: 92
title: Discovery relevance scoring
nav_exclude: true
status: accepted
date_proposed: 2026-06-19
date_resolved: 2026-07-03
assumes: [30]
supersedes: []
superseded_by: []
---

# ADR-92: Discovery relevance scoring

## Context

Discovery candidates currently need ranking against the human's steering.
An LLM skill can rank candidates, but a deterministic scorer could provide an
auditable first ordering using embeddings, citation graph overlap, and topic-tag
overlap.

## Decision

Memoria ranks `analyze-gaps` discovery candidate attention against `steering.md`
with a deterministic scorer. The alpha.15 scorer uses title/token overlap,
source topic-tag overlap, and citation-relation weight. It writes the score,
factor breakdown, and channel into the candidate attention frontmatter.

Candidates with no steering overlap go to a separate `exploration` channel with
score `0`; they remain visible but are not falsely treated as lower-quality
ranked candidates. The scorer feeds triage only. It never accepts, rejects, or
captures candidate Works automatically.

## Consequences

- Reduces LLM ranking cost and makes the ordering auditable.
- Requires a maintained `steering.md` and conservative weights.
- Can become misleading if the steering file drifts from the human's current agenda.

## When this matters

The discovery loop is live and morning triage exceeds 15 minutes because
candidates are not pre-sorted by relevance.

## Alternatives considered

**Keep LLM ranking only.** Flexible, but less reproducible and more expensive.

**Use embedding similarity in alpha.15.** Deferred because candidate Works often
arrive with only provider title/ID metadata, so a model-backed semantic score
would look precise without enough text. Add it when candidate abstracts/full text
are reliably present.

**Use recency or citation count only.** Cheap, but weakly aligned with the human's
research priorities.

## Related

- **Related decisions / Depends on:** [ADR-129](129-layered-machine-judgment.md), [ADR-95](95-nightly-proactive-discovery-loop.md).
- **Tracking issue:** [#705](https://github.com/eranroseman/memoria-vault/issues/705).
