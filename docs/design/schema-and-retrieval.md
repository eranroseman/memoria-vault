---
topic: proposals
title: Schema and retrieval extensions
status: resolved-by-redesign  # D2/D3/D5 + Find/Search; reconcile any remainder
created: 2026-05-31
---

# Schema and retrieval extensions

Capabilities that make the vault's knowledge graph richer and more queryable.

---

## 1. Scenario-typed retrieval (relation type expansion)

**Status.** Base is adopted: ADR-8 added `supports` and `contradicts` as first-class frontmatter fields; ADR-9 added the contradictions dashboard. This proposal covers the *expansion* beyond that base.

**What.** Extend the typed-relation vocabulary beyond `supports` / `contradicts` to include `similar` (structural resemblance, not evidential support), and potentially `cross-domain` or `counter-intuitive`. Enables precise queries like "show me claims structurally similar to X" that the current base can't answer.

**Trade-offs.** Every new value requires: template update, Linter vocabulary check, dashboard surface. If the human doesn't type new links consistently, the field becomes noisy (some links typed, most not) and queries return incomplete answers, eroding trust.

**Adoption trigger.** Both must hold: (1) ≥ 200 claim notes with ≥ 500 inter-claim wikilinks, *and* (2) the human notices wanting "find similar" queries and resorting to manual backlink walks.

A further candidate value is **`uses-method`** — a methodological-provenance relation on a claim-note pointing to the method-note it operationalizes, enabling "find all claims that used measurement approach X." It composes with the `_aspects.method` field in §2 below: the aspect says *what* method a paper used; the typed relation says *which existing method note* a claim reuses. Sequence it after `similar` — it is only worth the typing discipline once method-notes are a populated, linked layer.

**Guard.** Adopt one value at a time. `similar` first. Earn `cross-domain` (and `uses-method`) only if `similar` proves useful. Do not adopt the full PARNESS four-value taxonomy from day one — it was designed for ML/science workflows and may be wrong-shaped for knowledge work.

---

## 2. MASSW-aligned paper-note aspects

**What.** Add three structured `_aspects.*` fields to the paper-note template: `_aspects.key_idea`, `_aspects.method`, `_aspects.outcome`. Adapted from the MASSW schema (Zhang et al. 2024). These fields are agent-populated at ingest, human-correctable at review, and queryable via Dataview — enabling searches like "find all papers whose method is X."

The other two MASSW fields (`context` and `projected_impact`) are intentionally skipped: `context` overlaps with `topic:` and the existing summary; `projected_impact` requires post-publication evidence that ingest doesn't have.

**Trade-offs.** Adds LLM calls at ingest (one per paper for aspect extraction). Aspects extracted from an abstract are lower quality than from the full text; Marker-extracted body text improves accuracy when available.

**Extraction mechanism.** For papers whose method or outcome is carried by a figure or table rather than prose, Hermes's `vision_analyze` reads the figure/table directly — making `_aspects.method` / `_aspects.outcome` figure-informed rather than abstract-only. It is available now but not wired into the v0.1 ingest pipeline; this proposal is the natural place it gets adopted (the [ingest reference](../../../docs/reference/ingest.md) notes it as an available extraction path).

**Adoption trigger.** The Librarian is regularly ingesting papers *and* the human notices wanting to filter by method or outcome and resorting to reading full summaries.

---

## 3. Exploration-trace capture

**What.** When a Mapper scope or gap report is produced, also capture the *rejected directions* and *dead ends* from the research exploration — the paths that were tried and found unproductive. Stored as a structured artifact alongside the corpus map, not in the canonical knowledge layers. Based on ARA's finding that narrative publication discards the "failure knowledge" that could prevent repeating failed directions.

**Trade-offs.** Requires a convention for what counts as a "rejected direction" worth recording. Adds artifact management to Mapper's output contract. Risk of over-recording: if every negative result is captured, the artifact becomes noise.

**Adoption trigger.** The human notices repeating a direction they had already explored and finding nothing new — the "I'm sure I checked this before" failure mode.

**Guard.** Record rejected directions at the project level only, not globally. A dead end for one project may be productive for another. Never auto-promote exploration traces into canonical knowledge layers.
