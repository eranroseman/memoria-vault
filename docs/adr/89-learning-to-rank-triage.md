---
topic: decisions
id: 89
title: Learning-to-rank triage
status: proposed
date_proposed: 2026-06-19
date_resolved:
assumes: [30, 54]
supersedes: [59]
superseded_by: []
---

# ADR-89: Learning-to-rank triage

## Context

Triage ordering is personalized: the same candidate can be valuable or noise
depending on the human's prior keep/discard decisions and current research focus.
LLM tournament ranking is useful as a cold start, but it is expensive and less
auditable than a trained ranker once enough human decisions exist.

## Proposal

Memoria may train a learning-to-rank model, such as LightGBM LambdaRank, over the
human's past triage decisions to order future candidates. The scalar ordering or
LLM tournament remains the cold-start path until enough training data exists.

## Consequences

- Produces a cheaper, reproducible, personalized ordering after sufficient data.
- Requires stored training examples, evaluation, and drift monitoring.
- Poor early training data can make the ranking confidently wrong.

## When this matters

The human has made at least 300 triage decisions and notices that triage ordering
feels generic or unconditional on research priorities.

## Alternatives considered

**Keep LLM tournament ranking.** Better cold-start behavior, but high cost and low
auditability at scale.

**Use a fixed heuristic ranker only.** Cheap and deterministic, but unlikely to
learn the human's actual research preferences.

## Related

- **Supersedes:** [ADR-59](59-classical-method-displacements.md).
- **Related decisions / Depends on:** [ADR-30](30-deterministic-ingest-pipeline.md), [ADR-54](54-two-decision-kinds-batch-worklists.md).
- **Tracking issue:** [#702](https://github.com/eranroseman/memoria-vault/issues/702).
