---
title: Document types and epistemic roles
parent: Knowledge
grand_parent: Explanation
nav_order: 1
---

# Document types and epistemic roles

The vault's types are not arbitrary — each one answers a different question about who created the content, from whose perspective, and what status it has in the knowledge system. The deepest split is between the **Catalog** (structured entity records, built mechanically) and **Notes** (prose, written by someone). Understanding that split matters more than memorizing the type list.

---

## Entities vs notes: Luhmann's two boxes

The Catalog/Notes split revives Luhmann's two-box system: he kept a **bibliographic index** (who wrote what, where) physically separate from the **main slip-box** (his own thinking). Memoria does the same (see [Intellectual foundations](../overview/intellectual-foundations.md#luhmanns-zettelkasten)):

- **`catalog/` — entity records.** Structured facts about things in the world: a paper's DOI and authors, a person's ORCID, a venue's ISSN. Built by the **ingest operation** from metadata APIs, surfaced through Obsidian Bases, not review-gated — they are extractions of given facts, not judgments. Entities carry `relationships` (cited-by, authored-by, published-in): **given** connections the operation derives mechanically ([ADR-52](../../adr/52-links-vs-relationships.md)).
- **`notes/` — prose.** What a source says, what you think, how it all hangs together. Written by the PI or proposed by an agent. Notes carry `links:` — **authored** connections (supports, contradicts, hub membership) that an agent may propose but only the PI confirms.

"Relationships are given; links are authored." A connection between two entities is always a relationship; `links:` endpoints are always notes. Keeping the two boxes separate is what lets the mechanical half run ungated while the judgment half stays human.

---

## The six entity types

All in `catalog/`, all operation-built, all Base-backed: the bibliographic records — `paper`, `person`, `organization`, `venue`, `dataset`, `repository` — each keyed on stable IDs (a DOI, an ORCID, an ISSN) and carrying `relationships`. The exhaustive field lists live in [Document types](../../reference/document-types.md#catalog-entities-6).

An entity record never contains anyone's reading of the source — that is what a source *note* is for. The same paper is therefore two files: the `paper` entity (the bibliographic fact) and, if the PI reads it, a `source` note in `notes/sources/` that points back at the entity.

---

## The four note-document types

### Source notes: describing the world

A **`source`** note records what a source says — the brief, the key concepts, the limitations, the critique. It is written from an outside perspective: a source note never says what the PI thinks; it says what the source argues. That constraint is the mechanism that makes citation tracing work. If source notes expressed opinions, the boundary between "what the source says" and "what I think" would collapse, and provenance would become unverifiable.

A source note is one prose type regardless of whether the entity behind it is a paper, repository, dataset, report, or other source. Identification lives on the Catalog entity; the prose record stays focused on what the source says.

### Claim notes: the synthesis atom

A **`claim`** is one durable assertion in the PI's own words, linked to the sources that support it. It is the most important document type and the one that distinguishes a research vault from a document store. A vault full of source notes is a bibliography with annotations; a vault with interlinked claims is a knowledge graph the PI can write from.

Claims live in `notes/claims/` — a **review-gated zone** (🔒): agents draft claim *stubs* into staging, but the canonical claim is human-made. The discipline is atomicity — one claim per note, Luhmann's one-idea-per-slip rule — because wikilinks citing a multi-claim note are ambiguous, and a multi-claim note cannot be cleanly superseded when evidence changes. The test: if the title contains an "and" doing real conceptual work, it is two notes.

Claims carry `maturity` — a soft, PI-set signal of how *developed* the claim is, never a gate: a `seedling` claim is fully `current` ([ADR-50](../../adr/50-universal-lifecycle-and-maturity.md)). The values and the "signal, not a gate" rule are owned by [Why promotion is gated](promotion-model.md); the field is defined in [Frontmatter fields](../../reference/frontmatter.md).

### Hubs: authored navigation

A **`hub`** is a curated, annotated view of an area: what it is about, what matters most in it, and where it needs work. Hubs live in `notes/hubs/` — also gated 🔒, because a hub is an act of judgment about what belongs together, not a query result. Agents can propose additions; the PI curates.

### Fleeting notes

A **fleeting note** (`type: fleeting`) is raw capture — a thought, a URL, a quote — recorded before deciding what to do with it (`origin:` records whether a human or an agent wrote it). Fleeting notes are either distilled or archived; they don't persist as knowledge. Registers are Bases views, not a note type.

---

## The five card types

The **Inbox** (`inbox/`) is the agent→human message category — the signal end of every background loop ([ADR-51](../../adr/51-inbox-category-and-honesty-card.md)). Its five types are *transient cards*, not knowledge, and they sort into three shapes by epistemic role: **proposals** to judge (`candidate`, `gap`), **verification cards** to adjudicate (`flag`, `alert`), and a **work prompt** for work waiting on the PI (`work-prompt`). The exhaustive list — required fields, who raises each — lives in [Document types](../../reference/document-types.md#inbox-cards-5).

A card awaiting you is simply in the `proposed` state — there is no separate `review-request` type. Cards carry the honesty-card fields rather than verdicts; see [The honesty card](../kanban-board/card-schema.md).

---

## Why the distinctions matter

**Provenance.** If a source note could contain the PI's claims, "what does this paper say?" gets mixed with "what do I think about it?", and the Peer-reviewer cannot trace citations in a draft back to what sources actually said.

**Agent permissions.** The boundary follows the epistemic roles: agents (and the ingest operation) build entity records and propose source-note material, but `notes/claims/` and `notes/hubs/` are gated — recording what a source says is bookkeeping; asserting the PI's synthesis is not delegable.

**Lifecycle subsets.** Every type uses a subset of the one universal lifecycle chain, declared in its schema file under `.memoria/schemas/types/`; the chain and its values are defined in [Frontmatter fields](../../reference/frontmatter.md). The subset encodes the epistemic shape: entities are born `current` (facts don't await approval); source notes start `proposed` (awaiting reading); claims exist only once the PI makes them `current`.

---

## Related

- Why folders carry the type and frontmatter carries the state: [Lifecycle, not topic — and state, not folders](lifecycle-over-topic.md)
- How material crosses the review gate: [Why promotion is gated](promotion-model.md)
- The *how* of note bodies: [Note body structure](note-body-structure.md)
- The card format in depth: [The honesty card](../kanban-board/card-schema.md)
- Complete type reference (fields, templates): [Document types](../../reference/document-types.md)
