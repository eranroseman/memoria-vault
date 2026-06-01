# Screening protocol

Fill this in **before** running a pre-ingest screening pass. Required for a PRISMA-compliant
review and as ASReview's eligibility record. Only relevant in **systematic-review mode**
(see ADR-12 / ADR-19); a curated corpus under ~200 papers does not need it — the normal
`find → ingest` path handles snowballing at that scale.

> **Where screened sources land.** Included candidates enter the normal pipeline as candidate
> cards in `10-inbox/03-candidates/`; the Librarian then ingests confirmed ones into
> `20-sources/`. This protocol is the *upstream* record that governs which candidates get that far.

---

## Review metadata

| Field | Value |
| --- | --- |
| Review title | |
| Project ID | |
| Protocol date | YYYY-MM-DD |
| Reviewer | |
| Review type | Scoping / Systematic / Rapid |

## Research question

*State the question the screening is intended to answer.*

## Inclusion criteria

1.
2.
3.

## Exclusion criteria

1.
2.
3.

## Database sources

| Database | Search date | Records retrieved |
| --- | --- | --- |
| PubMed | | |
| ACM Digital Library | | |
| Scopus | | |
| arXiv | | |
| Other | | |

## Search strings

### PubMed

```text
```

### ACM DL

```text
```

## PRISMA decision log

| Stage | Records | Notes |
| --- | --- | --- |
| Identified (total across databases) | | |
| Duplicates removed | | |
| Screened (title/abstract) | | |
| Excluded (title/abstract) | | |
| Full text assessed | | |
| Excluded (full text) | | |
| **Included** | | |

## Screening decisions

Track individual exclusion reasons below, or use the Zotero RIS-tag method
(`ASReview_relevant` / `ASReview_irrelevant` / `ASReview_not_seen`):

| Citekey / DOI | Decision | Exclusion reason | Notes |
| --- | --- | --- | --- |
| | | | |

---

**Related:** [Run a systematic review](https://eranroseman.github.io/memoria-vault/how-to-guides/sources/run-a-systematic-review/) (the workflow that consumes this protocol);
ADR-12 (systematic-review mode) and ADR-19 (pre-ingest screening — PRISMA + ASReview);
ASReview + the Zotero RIS round-trip for the screening pass.
