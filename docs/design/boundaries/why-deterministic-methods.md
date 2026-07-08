---
title: Why deterministic methods
parent: Boundaries
grand_parent: Design
nav_order: 6
---

# Why deterministic methods

Every task Memoria performs is classified as deterministic, hybrid, or generative. The class determines which method to use, what the cost looks like, and what can be audited. Without this classification, every task gets routed to an LLM "because it's text" — and the system becomes expensive, slow, and untestable.

## The three classes

**Deterministic** tasks have a single right answer derivable from rules, regex, math, or graph algorithms. Citation token extraction, schema-version checking, link-candidate ranking, duplicate detection, and structural drift detection are all deterministic. The same vault state produces the same result on every run.

**Hybrid** tasks use a deterministic step to narrow the problem, then an LLM to
handle the residual judgment on the narrow result. Classification attention and
digest/report generation follow this pattern: metadata checks, checked input
refs, or ranked candidate sets bound what the runner may compose over.

**Generative** tasks have no fixed output and require open-ended composition. The Co-PI's conversation, the Writer's drafting, counter-outlines, and comparative-brief prose are generative. These are LLM-required and irreducibly so.

## The default test

If a regex, a graph algorithm, or a similarity threshold would produce the right answer most of the time, the task is deterministic or hybrid — not generative. The LLM enters only where the residual judgment genuinely requires it.

## Why the hybrid pattern dominates

The most common pattern in Memoria is deterministic narrowing followed by LLM enrichment on the narrow result:

```text
N candidates → deterministic ranking → K candidates (K ≪ N) → LLM composes over K
```

This matters beyond cost:

- **Auditability:** the deterministic step shows which candidates were selected,
  by what score, and why. The LLM prose is visible but opaque; selection is what
  the audit trail and eval fixtures measure.
- **Testability:** the deterministic layer has a single answer you can assert in tests. The LLM composition layer does not.

Concrete examples:

- **Checked BM25 retrieval**: checked retrieval documents -> deterministic BM25
  ranking -> bounded answer context.
- **DOI enrichment**: captured DOI or portable import -> provider metadata,
  field provenance, and graph edges -> checked catalog row or attention.
- **Digest/report generation**: DB-verdict-passing input refs -> runner output ->
  deterministic section and source-grounding checks before materialization.
- **Draft verification**: evidence markers, source-span refs, and code-warrant
  refs -> concrete findings or export readiness.

## Why this classification exists in the design

Without an explicit classification, there is pressure to route every task to an LLM because it's the easiest path. The explicit classification creates a forcing function: before adding a new skill or workflow, the designer must ask whether a deterministic method would suffice. This keeps the LLM's role contracted to where its judgment is actually load-bearing and keeps the rest of the system fast, cheap, and reproducibly testable.

## Related

- Which posture handles which task type: [Why operation postures, not a generalist agent](why-specialist-postures.md)
- The zero-LLM operation this rationale produces: [The Linter](../../explanation/execution/operations.md)
- [Retrieval and analysis methods](../../reference/retrieval-and-analysis-methods.md) — the catalog of specific deterministic methods Memoria uses
