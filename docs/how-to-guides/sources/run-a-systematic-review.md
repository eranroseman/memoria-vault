---
title: Run a systematic review
parent: Sources
nav_order: 13
---

# Run a systematic review

Set up a PRISMA-compliant screening protocol and process the results into Memoria. Use this when you need a defensible, reproducible literature search — not for exploratory snowballing, which the normal [find → ingest](find-new-sources.md) path handles.

## Prerequisites

- Memoria installed and the Librarian profile running
- A defined, written research question
- Access to at least two literature databases (PubMed, ACM DL, Scopus, arXiv, etc.)
- [ASReview](https://asreview.nl/) installed if the title/abstract pool exceeds ~200 records

## Steps

**1. Create a screening-protocol note.**

In Obsidian: `Cmd-P → Templater: Insert template → screening-protocol`. The template is at `99-system/templates/screening-protocol.md`.

Fill in: review title, project ID, protocol date, reviewer, review type (Scoping / Systematic / Rapid).

**2. Write your research question and criteria.**

In the screening-protocol note, complete:

- **Research question** — one sentence, specific enough to determine inclusion at the abstract stage
- **Inclusion criteria** — 3–5 explicit conditions a source must meet
- **Exclusion criteria** — 3–5 explicit grounds for rejection

Commit the protocol before running any searches. A protocol written after seeing the results is not a protocol.

**3. Run database searches.**

Run your search string in each database. Record in the protocol table:

| Column | What to fill in |
|---|---|
| Database | PubMed, ACM DL, Scopus, arXiv, … |
| Search date | ISO date |
| Records retrieved | Integer count |

Export each result set to RIS or BibTeX. Combine into a single file and remove duplicates.

**4. Screen titles and abstracts.**

**Under ~200 records — screen manually:**

For each record, apply your inclusion/exclusion criteria. Mark decisions directly in the screening-protocol note's decision log table (`Citekey / DOI | Decision | Exclusion reason`).

**200+ records — use ASReview:**

```bash
asreview oracle combined_export.ris
```

Label records as relevant / irrelevant in the ASReview interface. When the active-learning curve flattens, export the labeled dataset. Map decisions back to the protocol decision log.

Either way, record `ASReview_relevant`, `ASReview_irrelevant`, or `ASReview_not_seen` as the Zotero RIS tag for each record before ingest — this preserves the screening provenance in Zotero.

**5. Full-text assess included records.**

For each record marked relevant at the abstract stage:

1. Retrieve the full text
2. Re-apply inclusion/exclusion criteria against the full paper
3. Record the final decision and any exclusion reason in the protocol

**6. Update the PRISMA counts.**

Complete the decision log table in the screening-protocol note:

| Stage | Fill in |
|---|---|
| Identified | Total records across all databases |
| Duplicates removed | |
| Screened (title/abstract) | |
| Excluded (title/abstract) | |
| Full text assessed | |
| Excluded (full text) | |
| **Included** | Final count for ingest |

**7. Ingest included sources.**

For each included paper:

1. Add to Zotero — Better BibTeX auto-assigns a citekey
2. Pin the citekey if needed: [Pin a citekey](pin-a-citekey.md)
3. Let the `.bib` auto-export trigger Librarian ingest, or run manually:

```bash
hermes -p memoria-librarian chat -s ingest
/ingest --source <citekey>
```

The paper-note lands in `20-sources/01-papers/` after classification.

## Verify

- The screening-protocol note has all PRISMA counts filled in
- Every included source has a paper-note in `20-sources/01-papers/`
- Every excluded source has a decision and reason recorded in the protocol
- The protocol note's `lifecycle` field is set to `current`

## Related

- Exploratory discovery (no protocol needed): [Find new sources](find-new-sources.md)
- After ingest, classify each paper: [Classify a source](classify-a-source.md)
- The screening-protocol template: `99-system/templates/screening-protocol.md`
- The adopt-on-demand decision: [ADR-16](../../../project-files/decisions/16-adopt-on-demand-for-reviews.md)
