# Vocabulary discipline

A vault that grows without vocabulary discipline accumulates a silent failure: the same concept gets different names in different notes, and Dataview queries return half the corpus on a topic while the human believes coverage is thin. This document explains why the three classification fields are separate, how vocabulary drift happens, and why the stabilization happens in stages.

For the exact field definitions, allowed values, and the `study_design` controlled vocabulary, see [reference/frontmatter.md](../../reference/frontmatter.md).

## Why three separate fields, not one

Memoria uses three distinct classification fields — `study_design`, `methods`, and `topic` — rather than one general-purpose tag field. The separation is not bureaucratic; it reflects that these three dimensions answer categorically different questions.

`study_design` captures research architecture: *how* a study was structured. `methods` captures specific techniques used. `topic` captures conceptual content: *what* the work is about. A query asking "show me all RCTs" is a question about `study_design`. A query asking "everything on sensemaking" is a question about `topic`. Routing these to the same field makes both queries unreliable — the field can't simultaneously be the answer to orthogonal questions.

The Linter's `schema-check` detector validates that field values match the defined vocabulary, but only after the vocabulary has been defined. Drift from a vocabulary that doesn't yet exist is invisible to the Linter.

## Why vocabulary stabilization is deferred

Early in a vault's life, forcing term consistency is counterproductive. The right terms emerge from reading — you don't know yet whether "opportune-moment" and "receptivity-detection" are the same concept until you've read enough papers to recognize the pattern. Premature consolidation locks in the wrong vocabulary.

The deliberate design is to accept provisional terms early and consolidate once enough corpus has accumulated to make the vocabulary decisions durable. At roughly fifty papers, reviewing and merging inconsistent terms is tractable. Before that, the cost of false consolidation — deciding two concepts are the same when they're not — is higher than the cost of deferring.

This is also why reference taxonomies (MeSH, ACM CCS, OpenAlex) are kept in the `_enrichment` namespace rather than in `topic`. Those taxonomies are too granular and inconsistently applied across databases to serve as Dataview query targets. The custom `topic` vocabulary is what the human queries; the API taxonomies are what the human browses.

## Why drift fails silently

Vocabulary drift — the same concept appearing as `topic: receptivity-detection` in some notes and `topic: opportune-moments` in others — produces no error. Queries return incomplete results; the human infers thin coverage when coverage is adequate; research directions are shaped by a false gap signal. The failure is invisible until the vocabulary is audited.

This is the class of failure the Linter's `schema-check` detector is designed to catch, but only after the canonical vocabulary is defined. Before the canonical list exists, drift is entirely silent. See [common-pitfalls.md](common-pitfalls.md) for the concrete failure scenario and how it compounds over time.

## Related

- The Linter's schema-check detector: [profiles/linter.md](../profiles/linter.md)
- The common-pitfalls scenario this addresses: [common-pitfalls.md](common-pitfalls.md)
- The how-to for the vocabulary: [manage-vocabulary.md](../../how-to-guides/maintenance/manage-vocabulary.md)
- Field definitions and the `study_design` controlled vocabulary: [reference/frontmatter.md](../../reference/frontmatter.md)
