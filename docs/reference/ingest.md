# Ingest routing

Type detection dispatch table, per-type enrichment sources, and content extraction paths for the Librarian's ingest pipeline. For the full step-by-step procedure see [how-to-guides/sources/capture-and-ingest.md](../how-to-guides/sources/capture-and-ingest.md).

---

## Type detection dispatch

Before any write, the Librarian identifies the input type and routes to the correct folder and template.

| Input signal | Detected type | Destination folder | Template |
| --- | --- | --- | --- |
| DOI or arXiv ID in `.bib` | Paper / preprint | `20-sources/01-papers/` | `paper.md` |
| `github.com/…` or `gitlab.com/…` URL | Repository | `20-sources/02-items/` | `item.md` |
| PyPI / npm / CRAN URL | Package | `20-sources/02-items/` | `item.md` |
| Product or vendor URL | Product | `20-sources/02-items/` | `item.md` |
| Standards body URL (IEEE, RFC, W3C) | Standard | `20-sources/02-items/` | `item.md` |
| ORCID or person name | Person | `20-sources/03-entities/01-people/` | `person.md` |
| ROR or institution name | Organization | `20-sources/03-entities/02-organizations/` | `organization.md` |
| Conference / journal name | Venue | `20-sources/03-entities/03-venues/` | `venue.md` |
| DOI not in `.bib` | Unknown | — | **Prompt human to add to Zotero first** |

**Paper vs. item rule.** The split keys on a **stable publication ID, not medium**: a source carrying a DOI or arXiv ID is a `paper-note` (`01-papers/`). Datasets, software, repos, products, and standards *without* a DOI or arXiv ID are `item-note`s (`02-items/`).

If the type is ambiguous, the Librarian asks before proceeding. The agent never creates a note in the wrong folder.

---

## Per-type enrichment

| Detected type | Metadata source | Content extraction | Cross-link checks |
| --- | --- | --- | --- |
| Article / preprint | OpenAlex + Semantic Scholar + PubMed | Marker extracts full text → `90-assets/extracts/<citekey>.md`; summary in note body | Authors → person-notes; cited works → existing paper citekeys |
| Repository | GitHub API (REST or GraphQL) | `README.md` + `CHANGELOG.md` retrieved; summary into "What it is" | Primary maintainer → person-note; org owner → organization-note |
| Package | PyPI / npm / CRAN API | Package description + project links | Maintainer → person-note; underlying repo → repo item-note |
| Product | Vendor URL via `rest-passthrough` or MarkItDown fallback | Homepage text → summary | Vendor org → organization-note (if applicable) |
| Standard | Standards body URL (IEEE, RFC, W3C) | MarkItDown for HTML standards docs | Issuing org → organization-note |
| Person | ORCID API + OpenAlex Authors | (none — entity note) | Co-authors derived from shared paper-notes; affiliations → organization-notes |
| Organization | ROR API + OpenAlex Institutions | (none — entity note) | Affiliated people → person-notes |
| Venue | OpenAlex Venues + DBLP | (none — entity note) | (none) |

**Content extraction fallback.** Marker handles PDFs; MarkItDown handles the long tail (HTML pages, Office documents, web standards). Extracted markdown lands in `90-assets/extracts/<citekey>.md`. Re-extraction is safe — overwriting the extract file does not affect the paper-note.

---

## Frontmatter fields written at ingest

Fields the Librarian populates on the new note at creation:

| Field | Value | Notes |
| --- | --- | --- |
| `type` | Detected type (see table above) | Set once; never changed. |
| `lifecycle` | `proposed` | Promoted to `current` by the human at [Classify](../how-to-guides/sources/classify-a-source.md). |
| `created` | Today's date | `updated` is set to the same date at creation. |
| `citekey` | From `.bib` | Paper notes only. |
| `doi` | From `.bib` or OpenAlex | Promoted from `_enrichment` once verified. |
| `extract_path` | `90-assets/extracts/<citekey>.md` | Paper notes only; populated after Marker runs. |
| `pdf_uri` | `zotero://open-pdf/library/items/<key>` | Paper notes only. |
| `zotero_uri` | `zotero://select/items/<key>` | Paper notes only. |
| `enriched_date` | Today's date | Updated by each enrichment pass. |
| `_proposed_classification` | Agent-proposed `topic`, `study_design`, `methods` | Reviewed and promoted by human at Classify. |
| `_enrichment` | Citation count, abstract, venue, OA status, stable IDs | Refreshed on schedule by Librarian. |

---

## Card states during ingest

| Card state | Trigger | Notes |
| --- | --- | --- |
| `ready` | Watcher fires on `.bib` change or file-system event; watcher-triggered cards skip `triage` | — |
| `running` | Dispatcher claims card (within 60 s of `ready`) | Librarian profile executes |
| `done` | Librarian completes; sets `review_status: requested`; `_proposed_classification` populated | Human advances to Classify |
| `blocked` | `max_retries` exhausted after repeated metadata fetch failures | Default retry limit: 3 |

For the step-by-step ingest procedure see [how-to-guides/sources/capture-and-ingest.md](../how-to-guides/sources/capture-and-ingest.md).

---

## Related

- The profile running the pipeline: [librarian.md](../explanation/profiles/librarian.md)
- The note types routing dispatches to: [note-types.md](../explanation/knowledge/note-types.md)
