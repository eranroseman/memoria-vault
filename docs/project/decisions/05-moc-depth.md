---
topic: decisions
id: 5
title: MOC depth
status: retired
date_proposed: 2026-05-15
date_resolved: 2026-05-27
supersedes: []
superseded_by: []
---

# ADR-5: MOC depth

## Context

Original question: how granular should MOCs be? Per topic, per project, per method? The early Memoria design carried this as an open question.

## Decision

**Retired.** The MOC creation thresholds in [linking-patterns.md](../../reference/linking-patterns.md#moc-creation-thresholds) cover the granularity question with concrete numeric rules:

- Topic MOC at ≥ 15–20 notes
- Domain MOC at ≥ 3 topic MOCs
- Child MOC split at > 20 claim notes + > 10 paper notes
- Project MOC: one per dissertation chapter or formal review

No separate decision is needed beyond following the thresholds.

## Consequences

- The original "MOC depth" framing is dissolved into the linking-patterns reference.
- The human consults the linking-patterns thresholds, not this ADR, when deciding MOC granularity.

## Alternatives considered

Keeping this as an open decision was considered briefly but rejected — the threshold rules in linking-patterns are concrete enough that there's nothing left to decide at the roadmap level.

## Related

- **Files affected:** [vault/linking-patterns.md](../../reference/linking-patterns.md#moc-creation-thresholds)
