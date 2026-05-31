---
topic: proposals
id: 17
title: Retriever / Scout as a separate profile
status: proposed
date_proposed: 2026-05-15
date_resolved:
supersedes: []
superseded_by: []
---

# ADR-17: Retriever / Scout as a separate profile

## Context

Split the Librarian profile into Retriever (broad discovery, candidate generation) and Librarian (ingest, enrichment, classification)? The split would let Retriever scale across more candidates without taxing Librarian's classification model with discovery-shape work.

## Decision

**Defer.** Keep Librarian unified until discovery volume genuinely overwhelms it.

## Consequences

- Librarian handles both `find` and `ingest` workflows — simpler to configure, single lane policy, single command catalog.
- At high discovery volume (e.g., the [discovery loop](discovery-loop.md) running at scale), Librarian's classifier and discovery scoring might compete for compute; if so, split then.
- A future split has a clean shape — Retriever owns `10-inbox/03-candidates/`, Librarian owns `20-sources/` — so the deferral isn't blocking anything.

## Alternatives considered

**Split now**: rejected — one more profile to configure, with no current bottleneck to motivate it.

**Always-unified**: rejected as a long-term answer — at enough scale, the two concerns diverge.

## Related

- **Workflows affected:** [Find](../../docs/how-to-guides/sources/find-new-sources.md), [Ingest](../../docs/how-to-guides/sources/capture-and-ingest.md)
- **Files affected:** [profiles/README.md](../../explanation/profiles/README.md), [profiles/librarian.md](../../explanation/profiles/librarian.md)
