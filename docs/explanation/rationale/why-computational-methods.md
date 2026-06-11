---
title: Why Memoria uses deterministic methods alongside LLMs
parent: Design rationale
nav_order: 6
---

# Why Memoria uses deterministic methods alongside LLMs

Every task Memoria performs is classified as deterministic, hybrid, or generative. The class determines which method to use, what the cost looks like, and what can be audited. Without this classification, every task gets routed to an LLM "because it's text" — and the system becomes expensive, slow, and untestable.

## The three classes

**Deterministic** tasks have a single right answer derivable from rules, regex, math, or graph algorithms. Citation token extraction, schema-version checking, link-candidate ranking, duplicate detection, and structural drift detection are all deterministic. The same vault state produces the same result on every run.

**Hybrid** tasks use a deterministic step to narrow the problem, then an LLM to handle the residual judgment on the narrow result. `_proposed_classification`, `cite-check`, and the `[!brief]` callout all follow this pattern: a classifier or similarity search produces a ranked candidate set; an LLM composes over that small set rather than the whole vault.

**Generative** tasks have no fixed output and require open-ended composition. The co-PI's conversation, the Writer's drafting, counter-outlines, and comparative-brief prose are generative. These are LLM-required and irreducibly so.

## The default test

If a regex, a graph algorithm, or a similarity threshold would produce the right answer most of the time, the task is deterministic or hybrid — not generative. The LLM enters only where the residual judgment genuinely requires it.

## Why the hybrid pattern dominates

The most common pattern in Memoria is deterministic narrowing followed by LLM enrichment on the narrow result:

```text
N candidates → deterministic ranking → K candidates (K ≪ N) → LLM composes over K
```

This matters for two reasons beyond cost. First, the deterministic step is auditable — you can show which candidates were selected, by what score, and why. The LLM's prose is visible but opaque; the selection is what the audit trail and the fleet-health accept/reject ratios actually measure. Second, it makes the system testable: the deterministic layer has a single right answer you can assert in a test; the LLM's composition layer doesn't.

Concrete examples:

- **`[!suggestions]`**: 5,000 vault notes → top-10 candidates by weighted similarity → optional LLM explanation per candidate. The LLM works on 10, not 5,000.
- **`cite-check`**: 80 claims in a draft → citekey resolution + embedding similarity score per pair → LLM judges only the middle band (similarity 0.4–0.75). Above 0.75 auto-clean; below 0.4 auto-fail.
- **`_proposed_classification`**: new paper note → small classifier proposes labels with confidence → if confidence > 0.85, accept; else fall back to LLM proposal.

## Why this classification exists in the design

Without an explicit classification, there is pressure to route every task to an LLM because it's the easiest path. The explicit classification creates a forcing function: before adding a new skill or workflow, the designer must ask whether a deterministic method would suffice. This keeps the LLM's role contracted to where its judgment is actually load-bearing and keeps the rest of the system fast, cheap, and reproducibly testable.

## Related

- [Callouts](../obsidian/callouts.md) — how the hybrid pattern produces callout content
- Which profile handles which task type: [Why specialist profiles, not a generalist agent](why-specialist-profiles.md)
- The zero-LLM engine this rationale produces: [The Linter](../engines/README.md)
- [Retrieval and analysis methods](../../reference/computational-toolbox.md) — the catalog of specific deterministic methods Memoria uses
