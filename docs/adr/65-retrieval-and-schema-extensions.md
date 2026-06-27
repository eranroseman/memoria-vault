---
topic: decisions
id: 65
title: Retrieval and schema extensions
nav_exclude: true
status: superseded
date_proposed: 2026-06-11
date_resolved: 2026-06-19
assumes: [52, 30]
supersedes: []
superseded_by: [98, 99, 100]
---

# ADR-65: Retrieval and schema extensions

## Superseded

This proposal bundle is split into one ADR per retrieval/schema extension:

- [ADR-98](98-relation-vocabulary-expansion.md): Relation-vocabulary expansion.
- [ADR-99](99-massw-aligned-paper-aspects.md): MASSW-aligned paper aspects.
- [ADR-100](100-exploration-trace-capture.md): Exploration-trace capture.

## Related

- **Related decisions / Depends on:** [ADR-52 (links vs relationships)](52-links-vs-relationships.md) (the typed-relationship base this extends and the split this respects), [ADR-30 (ingest pipeline)](30-deterministic-ingest-pipeline.md) (where `_aspects` are populated)
- **Original tracking issues:** [#415](https://github.com/eranroseman/memoria-vault/issues/415)
  and [#611](https://github.com/eranroseman/memoria-vault/issues/611).
