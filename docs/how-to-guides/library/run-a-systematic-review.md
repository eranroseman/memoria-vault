---
title: Run a systematic review
parent: Library
grand_parent: How-to guides
nav_order: 3
---

# Run a systematic review

Set up a PRISMA-style screening protocol and process included sources into
Memoria. Use this when you need a defensible literature search; for ordinary
exploration, capture sources one at a time.

This is a manual procedure. Memoria captures the included sources, but you own
the search strategy, screening decisions, and protocol record.

## Prerequisites

- Memoria installed with a working CLI/runtime workspace
- A defined, written research question
- Access to at least two literature databases such as PubMed, ACM DL, Scopus, or arXiv
- Exportable BibTeX or CSL files from your literature databases or reference
  manager — stable citekeys and source metadata keep batch capture reproducible
- [ASReview](https://asreview.nl/) installed if the title/abstract pool exceeds ~200 records

## Steps

**1. Create a protocol note.**

Author it as a project note or protocol note attached to the review work.
Record the review title, protocol date, reviewer, and review type.

**2. Write your research question and criteria.**

Write your research question, inclusion criteria, and exclusion criteria using
your own systematic-review method, then record them in the protocol note.
Commit the protocol before running any searches — a protocol written after
seeing the results is not a protocol.

**3. Run database searches.**

Run your search strategy in each database using your own method. Record
database, search date, and records retrieved in the protocol note, then
export, combine, and deduplicate the result sets into one RIS or BibTeX file —
that file feeds screening in the next step.

**4. Screen titles and abstracts.**

Under roughly 200 records, screen manually: apply your criteria per record and
log each decision in the protocol note.

**200+ records — use ASReview:**

```bash
asreview oracle combined_export.ris
```

Label records in the ASReview interface; when the active-learning curve
flattens, export the labeled dataset and map decisions back to the protocol log.
Either way, preserve each record's screening outcome in the protocol before
import so the provenance survives.

**5. Full-text assess included records.**

Full-text screen each record marked relevant at the abstract stage using your
own criteria; record the final decision and any exclusion reason in the
protocol note.

**6. Update the PRISMA counts.**

Complete your PRISMA flow-diagram counts using your own method, then record
the final counts in the protocol note.

**7. Capture the included sources.**

Export each included paper to BibTeX or CSL, then import it through the standard
portable intake path ([Capture and ingest a source](capture-and-ingest.md)). The
capture/enrichment flow creates an unchecked SQLite Work row and raises attention
when provider evidence or full text is missing. For a protocol-screened paper,
the keep decision is already made; finish enrichment/full-text acquisition,
record the protocol outcome, and resolve the resulting attention item.

## Verify

- The protocol note has all PRISMA counts filled in
- Every included source has a catalog Work row with a stable `work_id`
- Every excluded source has a decision and reason recorded in the protocol

## Related

- The intake path per paper: [Capture and ingest a source](capture-and-ingest.md)
