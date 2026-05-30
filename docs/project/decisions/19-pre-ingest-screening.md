---
topic: decisions
id: 19
title: Pre-ingest screening layer (PRISMA + ASReview)
status: proposed
date_proposed: 2026-05-15
date_resolved:
supersedes: []
superseded_by: []
---

# ADR-19: Pre-ingest screening layer (PRISMA + ASReview)

## Context

Pre-ingest screening differs from `find` in scale (200–5000 candidates vs. 10–200), trigger (one-time vs. ongoing), and eligibility formality (explicit [PRISMA](../../reference/glossary.md#external-tools-and-standards) criteria vs. implicit relevance). For formal scoping or systematic reviews, a structurally separate workflow is needed.

## Decision

**Adopt when starting a formal scoping or systematic review.** Use [ASReview](../../reference/glossary.md#external-tools-and-standards) for ranking; export existing vault papers as priors via `hermes run export prior-labels`. Keep the two pipelines (find vs. pre-ingest screening) separate but share the candidate frontmatter format from [ADR-21](21-shared-candidate-frontmatter.md).

## Consequences

- Day-to-day `find` stays lightweight — PRISMA screening only spins up for a formal review.
- A formal review gets ASReview ranking and explicit PRISMA criteria exactly when the protocol calls for them.
- Shared candidate frontmatter (ADR-21) means a single Dataview query covers both pipelines.

## Alternatives considered

**Use `find` for both**: rejected — `find` is optimized for low-volume ongoing leads, not 500-candidate one-time database exports. The workflow shapes are different.

**Build a unified pipeline**: See [adopt-on-demand cluster rationale](adopt-on-demand-for-reviews.md).

## Related

- **Part of:** [Adopt-on-demand: systematic-review tooling](adopt-on-demand-for-reviews.md) — the shared rationale, plus the other three members (ADR-12, ADR-18, ADR-20).
- **Consumes:** [ADR-21 shared candidate frontmatter](21-shared-candidate-frontmatter.md) — the screening pipeline reads this schema.
- **Workflows affected:** [Find](../../how-to/workflows/upstream/find.md)
- **Files affected:** [profiles/librarian.md](../../explanation/profiles/librarian.md)
