---
topic: decisions
id: 91
title: Classical prose metrics for the export gate
nav_exclude: true
status: proposed
date_proposed: 2026-06-19
date_resolved:
assumes: [14, 62]
supersedes: []
superseded_by: []
---

# ADR-91: Classical prose metrics for the export gate

## Context

The export gate needs to catch prose quality issues, but many symptoms are
mechanical: readability, repetition, sentence length, passive-voice ratio, and
citation density. An LLM judge can assess coherence and tone, but it should not be
the first or only tool for deterministic prose signals.

## Proposal

Memoria may run classical prose metrics before the LLM-judge export gate. Metrics
may include Flesch-Kincaid readability, passive-voice ratio, citation density,
n-gram repetition, and sentence-length outliers.

## Consequences

- Adds cheap, reproducible signals before generative review.
- Risks false alarms if thresholds are not tuned to scholarly prose.
- Keeps the LLM judge responsible for coherence and tonal drift rather than
  replacing it.

## When this matters

The LLM-judge export gate is live and recurring false alarms on structural prose
issues dominate the report.

## Alternatives considered

**Keep export review purely LLM-judged.** Simpler, but wastes generative review on
deterministic symptoms.

**Block exports on prose metrics alone.** Rejected because metrics are symptoms,
not final quality judgments.

## Related

- **Related decisions / Depends on:** [ADR-126](126-four-type-knowledge-model.md), [ADR-62](62-measurement-and-verification-harnesses.md).
- **Tracking issue:** [#704](https://github.com/eranroseman/memoria-vault/issues/704).
