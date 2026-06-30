---
topic: decisions
id: 90
title: Claim-sentence classification
nav_exclude: true
status: proposed
date_proposed: 2026-06-19
date_resolved:
assumes: [30, 54]
supersedes: []
superseded_by: []
---

# ADR-90: Claim-sentence classification

## Context

Claim extraction can waste LLM attention on full-paper text when only a small
subset of sentences are plausible claims. A classical rhetorical-zone classifier
or structured heuristic pass could narrow the candidate set before any generative
judgment.

## Proposal

Memoria may add claim-sentence classification before LLM claim proposal. Candidate
methods include CoreSC/ART-style rhetorical-zone classifiers and heuristics based
on citations, hedging, and numeric claims.

## Consequences

- Reduces LLM input size and can improve precision of proposed claim notes.
- Requires labeled or validated examples and false-positive monitoring.
- Bad classification can hide useful claims before the LLM ever sees them.

## When this matters

Agent-proposed candidate claim notes are being piloted and the LLM false-positive
rate on non-claim sentences is producing meaningless candidates.

## Alternatives considered

**Send full paper text to the LLM.** Simpler, but costlier and less auditable.

**Use classifier output as final truth.** Rejected because claim status still needs
review and context; the classifier only narrows the candidate set.

## Related

- **Related decisions / Depends on:** [ADR-30](30-deterministic-ingest-pipeline.md), [ADR-54](54-two-decision-kinds-batch-worklists.md).
- **Tracking issue:** [#703](https://github.com/eranroseman/memoria-vault/issues/703).
