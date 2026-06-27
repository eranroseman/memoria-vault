---
title: Run a systematic review
parent: Library
grand_parent: How-to guides
nav_order: 7
---

# Run a systematic review

Set up a PRISMA-compliant screening protocol and process the results into Memoria. Use this when you need a defensible, reproducible literature search — not for exploratory discovery, which the normal [find → capture](find-new-sources.md) path handles.

> **Status: a manual procedure.** There is no "run systematic review" command and no screening template. The workflow composes existing pieces — a protocol note you author, your own database searches, optional [ASReview](https://asreview.nl/) for large pools, and the standard capture pipeline. Every step below works today; the protocol discipline is yours to keep.

## Prerequisites

- Memoria installed and the Librarian lane running
- A defined, written research question
- Access to at least two literature databases (PubMed, ACM DL, Scopus, arXiv, …)
- Zotero + Better BibTeX — batch ingest without a `.bib` backbone is not worth the friction
- [ASReview](https://asreview.nl/) installed if the title/abstract pool exceeds ~200 records

## Steps

**1. Create a protocol note.**

Author it as a project or source note attached to the review work. Record: review title, protocol date, reviewer, review type (Scoping / Systematic / Rapid).

**2. Write your research question and criteria.**

In the protocol note, complete:

- **Research question** — one sentence, specific enough to determine inclusion at the abstract stage
- **Inclusion criteria** — 3–5 explicit conditions a source must meet
- **Exclusion criteria** — 3–5 explicit grounds for rejection

Commit the protocol before running any searches. A protocol written after seeing the results is not a protocol.

**3. Run database searches.**

Run your search string in each database. Record in a protocol table: database, search date, records retrieved. Export each result set to RIS or BibTeX, combine, and deduplicate.

**4. Screen titles and abstracts.**

**Under ~200 records — screen manually:** apply your criteria per record; log decisions in the protocol note's decision table (`Citekey / DOI | Decision | Exclusion reason`).

**200+ records — use ASReview:**

```bash
asreview oracle combined_export.ris
```

Label records in the ASReview interface; when the active-learning curve flattens, export the labeled dataset and map decisions back to the protocol log. Either way, tag each record's screening outcome in Zotero before ingest so the provenance survives.

**5. Full-text assess included records.**

For each record marked relevant at the abstract stage: retrieve the full text, re-apply the criteria, record the final decision and any exclusion reason.

**6. Update the PRISMA counts.**

Complete the protocol's flow table: identified → duplicates removed → screened → excluded (title/abstract) → full-text assessed → excluded (full text) → **included**.

**7. Capture the included sources.**

Add each included paper to Zotero, then capture it one per paper through the standard intake path ([Capture and ingest a source](capture-and-ingest.md)). The ingest operation builds the Catalog entity and raises the candidate card — for a protocol-screened paper, the keep decision is already made, so resolve each card to `current` and move on.

## Verify

- The protocol note has all PRISMA counts filled in and `lifecycle: current`
- Every included source has a Catalog entity in `catalog/papers/`
- Every excluded source has a decision and reason recorded in the protocol

## Related

- Exploratory discovery (no protocol needed): [Find new sources](find-new-sources.md)
- The intake path per paper: [Capture and ingest a source](capture-and-ingest.md)
- The adopt-on-demand decision: [ADR-16](../../adr/16-systematic-review-adopt-on-demand.md)
