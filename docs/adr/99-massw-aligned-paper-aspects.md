---
topic: decisions
id: 99
title: MASSW-aligned paper aspects
nav_exclude: true
status: accepted
date_proposed: 2026-06-19
date_resolved: 2026-07-03
assumes: [30]
supersedes: []
superseded_by: []
---

# ADR-99: MASSW-aligned paper aspects

## Context

Paper summaries do not always expose method or outcome in a queryable way.
MASSW-style aspects can make context, key idea, method, outcome, limitations,
and assumptions queryable, but weak extraction would add false structure.

## Decision

Memoria stores paper aspects in a SQLite `work_aspects` read-model table, not in
frontmatter. The alpha.15 table supports `context`, `key_idea`, `method`,
`outcome`, `limitation`, and `assumption`, with source ID, aspect text, anchor
text, check status, provider label, and update time.

Source capture and enrichment populate the table from structured CSL
`memoria.aspects`/`_aspects` payloads and from explicit Markdown sections in
the acquired full text. Checked Work search documents include the aspect block,
making aspects queryable through the existing Ask/Search path.

LLM extraction and figure-informed extraction stay out until there is a
calibrated extractor. `projected_impact` stays out because it needs evidence the
ingest path does not have.

## Consequences

- Improves filtering by method and outcome.
- Keeps machine-derived structure out of frontmatter.
- Explicit section/metadata extraction is conservative but misses implicit aspects.

## When this matters

The Librarian regularly ingests papers and the human wants to filter by method or
outcome, but must read full summaries to do it.

## Alternatives considered

**Adopt all MASSW fields.** Rejected because `projected_impact` needs
post-publication evidence.

**Wait for figure-informed extraction.** Rejected as a prerequisite because an
abstract-only slice can be useful independently.

**Write `_aspects.*` into source frontmatter.** Rejected because source metadata
is DB-owned in alpha.15, and derived fields should not churn authored files.

## Related

- **Related decisions / Depends on:** [ADR-30](30-deterministic-ingest-pipeline.md).
- **Tracking issue:** [#712](https://github.com/eranroseman/memoria-vault/issues/712).
