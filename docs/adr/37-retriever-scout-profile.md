---
topic: decisions
id: 37
title: Retriever / Scout as a separate profile
status: superseded
superseded_by: [48]  # one Librarian posture spans catalog·extract·link·map, find included (D27/D34)
assumes: []
date_proposed: 2026-05-15
date_resolved: 2026-06-10
supersedes: []
parent: Decisions
grand_parent: Explanation
nav_order: 37
---

# ADR-37: Retriever / Scout as a separate profile

## What

Split the Librarian into **Retriever** (broad discovery, candidate generation) and **Librarian** (ingest, enrichment, classification), so discovery can scale across more candidates without taxing the classification model with discovery-shape work.

## Why

At high discovery volume, one profile doing both `find` and `ingest` may have its classifier and its discovery scorer competing for the same compute and context.

## Trade-offs

- One more profile to configure (lane policy, command catalog, SOUL.md) with no current bottleneck to justify it.
- A unified Librarian is simpler: single lane, single command set.

## When this matters

Discovery volume genuinely overwhelms the unified Librarian — e.g. the [nightly discovery loop](61-nightly-discovery-loop.md) running at scale, where discovery scoring and classification visibly contend.


## Alternatives considered

**Split now.** Rejected: one more profile with no current bottleneck to motivate it.

**Stay unified forever.** Rejected as a long-term answer: at enough scale the two concerns diverge.

## Related

- **Workflows:** [Find](../how-to-guides/compile/find-new-sources.md), [Ingest](../how-to-guides/compile/capture-and-ingest.md)
- **Files:** [Profiles](../explanation/profiles/README.md), [The Librarian](../explanation/profiles/librarian.md)
