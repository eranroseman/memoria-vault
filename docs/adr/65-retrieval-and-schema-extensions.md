---
topic: decisions
id: 65
title: Retrieval and schema extensions
status: proposed
nav_exclude: true
date_proposed: 2026-06-11
date_resolved:
assumes: [52, 30]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 65
---

# ADR-65: Retrieval and schema extensions

## Context

The typed-relation base is adopted through
[ADR-52](52-links-vs-relationships.md): relationships are typed, queryable facts
distinct from ordinary wikilinks, and the contradictions dashboard consumes the
first `supports` / `contradicts` vocabulary. The
question is not whether these extensions are well-shaped but when they earn the typing
and ingest discipline they each demand: a half-populated typed field returns
incomplete answers and erodes trust, and aspect extraction adds an LLM call per paper.
This ADR is the settled home for those extensions; it adopts none until its trigger
fires.

## Proposal

Memoria should evaluate three retrieval/schema extensions separately:

- **Relation-vocabulary expansion.** Extend the typed-relation vocabulary (the
  deployed `link-suggest-claim` skill already proposes `supports` / `contradicts` /
  `extends`; the vocabulary is documentary — the Linter validates that targets
  resolve, not the relation key) to `similar` (structural resemblance, not evidential
  support), then `cross-domain` and `uses-method` (a methodological-provenance
  relation pointing a claim-note at the method-note it operationalizes — composing
  with `_aspects.method` below, which says *what* method a paper used while the
  relation says *which* method note a claim reuses). One value is adopted at a time,
  `similar` first; `cross-domain` and `uses-method` are earned only if `similar`
  proves useful. The full PARNESS four-value taxonomy is not adopted from day one — it
  was designed for ML/science workflows and may be wrong-shaped for knowledge work.
  `uses-method` is sequenced last, worthwhile only once method-notes are a populated,
  linked layer.
- **MASSW-aligned paper aspects.** Add `_aspects.key_idea`, `_aspects.method`,
  and `_aspects.outcome` to the paper template (adapted from MASSW, Zhang et al.
  2024) — agent-populated at ingest ([ADR-30](30-deterministic-ingest-pipeline.md)),
  human-correctable at review, Dataview-queryable. The other two MASSW fields are
  skipped: `context` overlaps `topic:` and the summary; `projected_impact` needs
  post-publication evidence ingest lacks. For papers whose method or outcome lives in
  a figure or table, a vision extraction path could read it directly, making the
  aspects figure-informed rather than abstract-only. No such `vision_analyze` path
  exists in the ingest pipeline today (the figure-informed variant is blocked on
  building/importing it, not merely on wiring an available one); the abstract-only
  `_aspects` slice is independent of it and can land first.
- **Exploration-trace capture.** When the Librarian's map lane produces a scope or gap report, also
  capture the *rejected directions* and *dead ends* as a structured artifact beside
  the corpus map (never in canonical knowledge layers), preventing re-exploration of
  failed paths. Rejected directions are recorded at the project level only — a dead
  end for one project may be productive for another — and never auto-promoted into
  canonical layers.

These build on the typed-relationship base of
[ADR-52](52-links-vs-relationships.md) and
respect the links-vs-relationships split of
[ADR-52](52-links-vs-relationships.md): untyped wikilinks remain first-class and
coexist with the expanded `links:` vocabulary.

## Consequences

- Each new relation value costs a template update, a Linter vocabulary check, and a
  dashboard surface; inconsistent typing makes the field noisy and queries incomplete.
- `_aspects` extraction adds one LLM call per paper at ingest; abstract-only aspects
  are lower quality than figure- or full-text-informed ones.
- Exploration-trace capture adds an artifact-management obligation to the map lane's output
  contract and risks over-recording if every negative result is captured.
- Recording these candidates keeps ADR-08's future-work pointer resolvable and
  anchors the not-yet-built figure-reading extraction path.

## When this matters

Per-release context, not gates:

- **`similar` (relation expansion):** both must hold — at least 200 claim notes with
  at least 500 inter-claim wikilinks, *and* the human notices wanting "find similar"
  queries and resorting to manual backlink walks. `cross-domain` / `uses-method` only
  after `similar` proves out.
- **`_aspects`:** the Librarian is regularly ingesting papers *and* the human notices
  wanting to filter by method or outcome and resorting to reading full summaries.
- **Exploration traces:** the human notices repeating an already-explored direction —
  the "I'm sure I checked this before" failure mode.

## Related

- **Related decisions / Depends on:** [ADR-52 (links vs relationships)](52-links-vs-relationships.md) (the typed-relationship base this extends and the split this respects), [ADR-30 (ingest pipeline)](30-deterministic-ingest-pipeline.md) (where `_aspects` are populated)
- **Tracking issue:** [#415](https://github.com/eranroseman/memoria-vault/issues/415) — proposal shaping and scheduling live on the issue.
