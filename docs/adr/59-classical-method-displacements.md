---
topic: decisions
id: 59
title: Classical method displacements over LLM calls
nav_exclude: true
status: superseded
date_proposed: 2026-06-11
date_resolved: 2026-06-19
assumes: [9, 30]
supersedes: []
superseded_by: [89, 90, 91, 92, 93, 94]
---

# ADR-59: Classical method displacements over LLM calls

## Superseded

This proposal bundle is split into one ADR per candidate displacement:

- [ADR-89](89-learning-to-rank-triage.md): Learning-to-rank for triage.
- [ADR-90](90-claim-sentence-classification.md): Claim-sentence classification.
- [ADR-91](91-classical-prose-metrics-export-gate.md): Classical prose metrics for the export gate.
- [ADR-92](92-discovery-relevance-scoring.md): Discovery relevance scoring.
- [ADR-93](93-keyphrase-extraction-tag-candidates.md): Keyphrase extraction for tag candidates.
- [ADR-94](94-record-linkage-entity-deduplication.md): Record linkage for entity deduplication.

## Related

- **Related decisions / Depends on:** [ADR-09 contradictions dashboard](09-contradictions-dashboard.md) (owns the NLI contradiction proposer); [ADR-30 deterministic ingest pipeline](30-deterministic-ingest-pipeline.md) (the deterministic discipline these displacements extend).
- **Source discussion:** [Why Memoria uses deterministic methods alongside LLMs](../explanation/rationale/why-computational-methods.md).
- **Original tracking issue:** [#409](https://github.com/eranroseman/memoria-vault/issues/409).
