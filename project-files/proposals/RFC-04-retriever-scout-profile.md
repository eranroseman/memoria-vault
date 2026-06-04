---
topic: proposals
id: RFC-04
title: Retriever / Scout as a separate profile
status: deferred
created: 2026-05-15
---

# RFC-04: Retriever / Scout as a separate profile

## What

Split the Librarian into **Retriever** (broad discovery, candidate generation) and **Librarian** (ingest, enrichment, classification), so discovery can scale across more candidates without taxing the classification model with discovery-shape work.

## Why

At high discovery volume, one profile doing both `find` and `ingest` may have its classifier and its discovery scorer competing for the same compute and context.

## Trade-offs

- One more profile to configure (lane policy, command catalog, SOUL.md) with no current bottleneck to justify it.
- A unified Librarian is simpler: single lane, single command set.

## Adoption trigger

Discovery volume genuinely overwhelms the unified Librarian — e.g. the [discovery loop](explorations/discovery-loop.md) running at scale, where discovery scoring and classification visibly contend.

## Guard

Keep Librarian unified until that bottleneck is real. The split has a clean future shape (Retriever owns `10-inbox/03-candidates/`, Librarian owns `20-sources/`), so deferring blocks nothing.

## Alternatives considered

**Split now.** Rejected: one more profile with no current bottleneck to motivate it.

**Stay unified forever.** Rejected as a long-term answer: at enough scale the two concerns diverge.

## Related

- **Workflows:** [Find](../../docs/how-to-guides/compile/find-new-sources.md), [Ingest](../../docs/how-to-guides/compile/capture-and-ingest.md)
- **Files:** [profiles/README.md](../../docs/explanation/profiles/README.md), [profiles/librarian.md](../../docs/explanation/profiles/librarian.md)
