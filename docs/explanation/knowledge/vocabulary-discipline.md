---
title: Vocabulary discipline
parent: Knowledge
grand_parent: Explanation
nav_order: 5
---

# Vocabulary discipline

A vault that grows without vocabulary discipline accumulates a silent failure: the same concept gets different names in different notes, and queries return half the corpus on a topic while the PI believes coverage is thin. This document explains why the classification facets are separate, how vocabulary drift happens, and why the stabilization happens in stages.

For the exact field definitions and allowed values, see [Frontmatter fields](../../reference/frontmatter.md).

## Why separate facets, not one tag field

Memoria classifies sources with two distinct facets — `research_area` and `methodology` — plus `topics` on claim notes, rather than one general-purpose tag field. The separation is not bureaucratic; the facets answer categorically different questions.

`methodology` captures research architecture: _how_ a study was structured (RCT, observational, qualitative, systematic review, simulation, …). `research_area` captures conceptual content: _what_ the work is about. A query asking "show me all RCTs" is a `methodology` question. A query asking "everything on sensemaking" is a `research_area` question. Routing both to the same field makes both queries unreliable — one field can't simultaneously be the answer to orthogonal questions.

The Linter's `schema-check` pass validates that facet values match the defined vocabulary, but only after the vocabulary has been defined. Drift from a vocabulary that doesn't yet exist is invisible to the Linter.

## Why vocabulary stabilization is deferred

Early in a vault's life, forcing term consistency is counterproductive. The right terms emerge from reading — you don't know yet whether "opportune-moment" and "receptivity-detection" are the same concept until you've read enough papers to recognize the pattern. Premature consolidation locks in the wrong vocabulary.

The deliberate design is to accept provisional terms early and consolidate once enough corpus has accumulated to make the vocabulary decisions durable. At roughly fifty papers, reviewing and merging inconsistent terms is tractable. Before that, the cost of false consolidation — deciding two concepts are the same when they're not — is higher than the cost of deferring.

This is also why source metadata corrections go through explicit Work updates:
catalog terms should land only when they match the controlled vocabulary. Claim
`topics` are human-extended, and that is where the discipline below applies.

## Why drift fails silently

Vocabulary drift — the same concept appearing as `topics: receptivity-detection` in some claims and `topics: opportune-moments` in others — produces incomplete query results even when the YAML is valid. The PI infers thin coverage when coverage is adequate; research directions are shaped by a false gap signal. The failure is invisible until `schema-check` or a vocabulary audit runs.

This is the class of failure the Linter's `schema-check` pass is designed to catch, but only after the canonical vocabulary is defined. Before the canonical list exists, drift is entirely silent. See [Common pitfalls](common-pitfalls.md) for the concrete failure scenario and how it compounds over time.

## Related

- The operation that validates the vocabulary: [Operations](../operations.md)
- The common-pitfalls scenario this addresses: [Common pitfalls](common-pitfalls.md)
- The how-to for the vocabulary: [Manage your topic vocabulary](../../how-to-guides/knowledge/manage-vocabulary.md)
- Field definitions: [Frontmatter fields](../../reference/frontmatter.md)
