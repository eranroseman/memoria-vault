---
topic: decisions
id: 93
title: Keyphrase extraction for tag candidates
nav_exclude: true
status: accepted
date_proposed: 2026-06-19
date_resolved: 2026-07-03
assumes: [30]
supersedes: []
superseded_by: []
---

# ADR-93: Keyphrase extraction for tag candidates

## Context

Memoria classifies paper metadata today, but controlled-vocabulary tag recall can
lag when new terms appear that a classifier has not seen. Keyphrase extraction can
surface candidate vocabulary terms without asking an LLM to invent tags.

## Decision

Memoria uses the existing `analyze-gaps` operation to surface tag candidates.
The alpha.15 implementation runs a deterministic stdlib phrase pass over checked
Work text, suppresses phrases already present in `system/vocabulary.md` or
checked frontmatter terms, and writes repeated off-vocabulary phrases as stable
unchecked Inbox candidate cards. It never writes tags directly.

KeyBERT, YAKE, or another extractor can replace the phrase pass only after real
corpus misses show this cheap pass is insufficient.

## Consequences

- Improves recall for vocabulary gaps and emerging terms without a new model
  dependency.
- Keeps candidate generation in the existing gap-analysis path instead of adding
  a second vocabulary scan.
- Extracted phrases remain candidates; the controlled vocabulary remains the
  authority.

## Alternatives considered

**Use only existing metadata topics.** Simpler, but can miss domain-specific terms
that appear in Work text.

**Add KeyBERT or YAKE now.** Rejected for alpha.15 because a new extractor
dependency is unnecessary until corpus evidence shows the deterministic pass
misses useful terms.

**Let the LLM freely create tags.** Rejected because it bypasses controlled
vocabulary discipline.

## Related

- **Related decisions / Depends on:** [ADR-129](129-layered-machine-judgment.md).
- **Tracking issue:** [#706](https://github.com/eranroseman/memoria-vault/issues/706).
