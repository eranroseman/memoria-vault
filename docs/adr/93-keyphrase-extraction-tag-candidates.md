---
topic: decisions
id: 93
title: Keyphrase extraction for tag candidates
status: proposed
date_proposed: 2026-06-19
date_resolved:
assumes: [30]
supersedes: [59]
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 93
nav_exclude: true
---

# ADR-93: Keyphrase extraction for tag candidates

## Context

Memoria classifies paper metadata today, but controlled-vocabulary tag recall can
lag when new terms appear that a classifier has not seen. Keyphrase extraction can
surface candidate vocabulary terms without asking an LLM to invent tags.

## Proposal

Memoria may use KeyBERT, YAKE, or a similar keyphrase extractor to propose tag
candidates, then map those phrases onto the human's controlled vocabulary. This
also requires defining the host tag-classification path it extends.

## Consequences

- Improves recall for vocabulary gaps and emerging terms.
- Adds another classifier/extractor to tune and validate.
- Extracted phrases remain candidates; the controlled vocabulary remains the
  authority.

## When this matters

A tag classifier has been active for at least three months and the human notices
recurrent vocabulary gaps.

## Alternatives considered

**Use only existing metadata topics.** Simpler, but can miss domain-specific terms.

**Let the LLM freely create tags.** Rejected because it bypasses controlled
vocabulary discipline.

## Related

- **Supersedes:** [ADR-59](59-classical-method-displacements.md).
- **Related decisions / Depends on:** [ADR-30](30-deterministic-ingest-pipeline.md).
- **Tracking issue:** [#706](https://github.com/eranroseman/memoria-vault/issues/706).
