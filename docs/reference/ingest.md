---
title: Ingest routing
parent: Reference
---

# Ingest routing

Type detection dispatch table, per-type enrichment sources, and content extraction paths for the Librarian's ingest pipeline. For the full step-by-step procedure see [Capture and ingest a source](../how-to-guides/compile/capture-and-ingest.md).

---

## Type detection dispatch

Before any write, the Librarian identifies the input type and routes to the correct folder and template.

| Input signal | Detected type | Destination folder | Template |
| --- | --- | --- | --- |
| DOI or arXiv ID in `.bib` | Paper / preprint | `20-sources/01-papers/` | `paper-note.md` |
| `github.com/…` or `gitlab.com/…` URL | Repository | `20-sources/02-items/` | `item-note.md` |
| PyPI / npm / CRAN URL | Package | `20-sources/02-items/` | `item-note.md` |
| Product or vendor URL | Product | `20-sources/02-items/` | `item-note.md` |
| Standards body URL (IEEE, RFC, W3C) | Standard | `20-sources/02-items/` | `item-note.md` |
| ORCID or person name | Person | `20-sources/03-entities/01-people/` | `person-note.md` |
| ROR or institution name | Organization | `20-sources/03-entities/02-organizations/` | `organization-note.md` |
| Conference / journal name | Venue | `20-sources/03-entities/03-venues/` | `venue-note.md` |
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
| Product | Homepage text via the ingest pipeline's MarkItDown extraction (HTML → Markdown) | Homepage text → summary | Vendor org → organization-note (if applicable) |
| Standard | Standards body URL (IEEE, RFC, W3C) | MarkItDown for HTML standards docs | Issuing org → organization-note |
| Person | ORCID API + OpenAlex Authors | (none — entity note) | Co-authors derived from shared paper-notes; affiliations → organization-notes |
| Organization | ROR API + OpenAlex Institutions | (none — entity note) | Affiliated people → person-notes |
| Venue | OpenAlex Venues + DBLP | (none — entity note) | (none) |

**Content extraction fallback.** Marker handles PDFs; MarkItDown handles the long tail (HTML pages, Office documents, web standards). Extracted markdown lands in `90-assets/extracts/<citekey>.md`. Re-extraction is safe — overwriting the extract file does not affect the paper-note. For a PDF that arrives **without a DOI** (so the OpenAlex/Semantic Scholar metadata path can't resolve it), GROBID recovers header and reference fields from the PDF itself. For figure- and table-heavy papers where the key result is an image rather than prose, Hermes's `vision_analyze` is an alternative extraction path — available, not wired into the v0.1 pipeline (see the [MASSW-aspects proposal](../design/retrieval-and-schema-extensions.md)).

### PDF extraction tools

Marker is the chosen extractor; the others are documented for the cases Marker isn't the best fit.

| Tool | Best for | Status |
| --- | --- | --- |
| **Marker** (Datalab) | Math-heavy papers; structured Markdown; `--use_llm` for accuracy | **Chosen** |
| **Docling** (IBM / Linux Foundation) | General PDFs + tables/figures; ships a `docling-mcp` server that drops in alongside the Zotero/Obsidian MCPs | Strong alternative for table/figure-heavy corpora |
| **PyMuPDF4LLM** | Fastest CPU-only path for clean, text-based PDFs | Pre-processing |
| **MarkItDown** (Microsoft) | Web pages, Office docs, HTML → Markdown | Current fallback (above) |
| **GROBID** (Inria) | Header / reference parsing for PDFs **without** a DOI (~0.87–0.90 F1) | Edge case only — not a pipeline stage |
| **Nougat** (Meta) | Math LaTeX | Unmaintained — avoid |

### Citation-format parsers — do not reimplement

Every citation workflow rests on mature parsers. Encoding, cross-referencing, and CSL edge cases are deep; use the library rather than hand-rolling.

| Format | Library | Note |
| --- | --- | --- |
| BibTeX / BibLaTeX | `bibtexparser` ≥ 2.0 | Handles encoding, special chars, cross-refs |
| RIS | `rispy` | Round-trip; used internally by ASReview |
| CSL-JSON | `citeproc-py` + `citeproc-py-styles` | CSL 1.0.1; plain/RST/HTML output |
| JATS XML (publisher) | `pubmed-parser` or `lxml` | PMC + most publishers |
| Convert between formats | `pypandoc` | Swiss-army knife across the above + Markdown |

### Identifier reconciliation helpers

For the enrichment path, when resolving an author, institution, or DOI to a stable identifier:

- `habanero.content_negotiation(doi, format="bibtex")` — one call covers DOI → BibTeX / CSL-JSON / RIS.
- [`drAbreu/alex-mcp`](https://github.com/drAbreu/alex-mcp) — author disambiguation (OpenAlex autocomplete + ORCID matching); installable as an MCP server companion.
- OpenRefine + ORCID/ROR/Wikidata — bulk entity reconciliation for person and organization notes.
- `python-orcid` (public search) and `pyalex.Institutions()["search"]` (→ ROR) — programmatic person/institution lookup.

---

## Frontmatter fields written at ingest

Fields the Librarian populates on the new note at creation:

| Field | Value | Notes |
| --- | --- | --- |
| `type` | Detected type (see table above) | Set once; never changed. |
| `lifecycle` | `captured` | The Tier-0 floor. The classification proposal promotes `captured → proposed`; the human promotes `proposed → current` at [Classify](../how-to-guides/compile/classify-a-source.md). |
| `ingest_status` | `tier0` → `enriched` → `complete` | Pipeline progress while `captured`; `needs-human` is the terminal floor after bounded failed re-ingest. See [Frontmatter fields](frontmatter.md#ingest_status-values-ingested-source-notes). |
| `created` | Today's date | `updated` is set to the same date at creation. |
| `citekey` | From `.bib` | Paper notes only. |
| `doi` | From `.bib` or OpenAlex | Promoted from `_enrichment` once verified. |
| `extract_path` | `90-assets/extracts/<citekey>.md` | Paper notes only; populated after Marker runs. |
| `pdf_uri` | `zotero://open-pdf/library/items/<key>` | Paper notes only. |
| `zotero_uri` | `zotero://select/items/<key>` | Paper notes only. |
| `enriched_date` | Today's date | Updated by each enrichment pass. |
| `_proposed_classification` | Agent-proposed `topic`, `study_design`, `methods` | Reviewed and promoted by human at Classify. |
| `_enrichment` | Citation count, abstract, venue, OA status, stable IDs | Refreshed on schedule by Librarian. |

**Note body.** Beyond frontmatter, ingest leads the new paper note with a `[!brief]` comparative-read callout the Librarian composes in the same pass — top-5 most-similar existing sources selected via `qmd` (deterministic), then an LLM narrative ("overlaps with / may contradict / new construct"). The Librarian writes it because only the Librarian writes `20-sources/`. See [Obsidian callouts](obsidian-callouts.md).

### Zotero fields without the Zotero API

The pipeline reads only the `.bib`, so Zotero-native fields come from the Better BibTeX export — no live Zotero API dependency:

- **`pdf_uri`** and the local PDF (for full-text extraction) are recovered from the bib `file` field — it carries the attachment path, whose `storage/<KEY>/` segment is the Zotero attachment key.
- **`zotero_uri`** (the select-into-Zotero link) needs the *parent* item key, which a normal `.bib` omits. Add it with a one-line Better BibTeX **postscript** (Zotero → Better BibTeX → Preferences → Export → Postscript), which the pipeline reads from a `zoteroselect` field:

  ```js
  if (Translator.BetterBibTeX || Translator.BetterBibLaTeX) {
    if (zotero.uri) {
      tex.add({ name: 'zoteroselect',
        value: zotero.uri.replace(/^https?:\/\/zotero\.org\/(?:users|groups)\/\w+\/items\/(\w+)$/,
                                  'zotero://select/library/items/$1') })
    }
  }
  ```

---

## Card states during ingest

| Card state | Trigger | Notes |
| --- | --- | --- |
| `ready` | Watcher fires on `.bib` change or file-system event; watcher-triggered cards skip `triage` | — |
| `running` | Dispatcher claims card (within 60 s of `ready`) | Librarian profile executes |
| `done` | Librarian completes; sets `review_status: requested`; `_proposed_classification` populated | Human advances to Classify |
| `blocked` | `max_retries` exhausted after repeated metadata fetch failures | Default retry limit: 3 |

For the step-by-step ingest procedure see [Capture and ingest a source](../how-to-guides/compile/capture-and-ingest.md).

---

## Durability: the capture-intake log and the two sweeps

Capture commits first. Before the gated note write, the capture entry point appends one line to `99-system/logs/capture-intake.jsonl` (un-gated — it is the durability anchor, so a failure anywhere downstream loses nothing):

```json
{"ts": "<ISO-8601 UTC>", "citekey": "<key>", "source": "zotero", "note_path": "20-sources/01-papers/<citekey>.md"}
```

Two backstops recover anything that stalls. Neither writes the vault — re-ingest must be **board-serialized** (single-lane WIP=1 makes find-or-create safe), so each is a detector that enqueues an **idempotent** re-ingest card (`hermes kanban create --idempotency-key reingest:<citekey>`). The board then provides dedup, backoff, and the failure circuit-breaker (the `needs-human` floor). Both live in `obsidian-paper-note/scripts/sweeps.py`:

| Sweep | Detects | Re-drives |
| --- | --- | --- |
| `--reconcile` | A capture logged in `capture-intake.jsonl` with no note on disk (the Tier-0 stub never landed) | Enqueues a re-ingest card so the first write is retried |
| `--retry` | A `captured` note stuck at `ingest_status: tier0` (Tier-1 never completed) | Enqueues a re-ingest card to re-run enrichment |

Run with `--dry-run` to report what would be enqueued without touching the board. The installer wires both passes as a deterministic, no-LLM cron (`memoria-sweeps`, every 15 minutes) that recovers stalled captures automatically.

---

## Related

- The profile running the pipeline: [The Librarian](../explanation/profiles/librarian.md)
- The note types routing dispatches to: [Note types and epistemic roles](../explanation/knowledge/note-types.md)
