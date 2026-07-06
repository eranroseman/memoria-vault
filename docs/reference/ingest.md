---
title: Ingest routing
parent: Pipelines and I/O
grand_parent: Reference
nav_order: 1
---

# Ingest routing

Worker capture starts the catalog record, but scholarly identifiers do not
become checked source rows before provider verification. Worker
`capture-source` stages DOI inputs as unchecked SQLite catalog rows plus
durable content/raw blobs under `.memoria/blobs/source-content/`; worker
`enrich-source` resolves required DOI providers, records provenance, and checks
the row only when provider and retraction checks pass.

The runtime helper `memoria_vault.runtime.capture.stage_catalog_source()` handles
source payloads: it records a capture run, writes raw and extracted text blobs,
writes source metadata into SQLite catalog state, and records derived
aspects/edges there. Portable BibTeX/CSL imports use the same unchecked SQLite
staging path. The PDF adapter `capture_pdf_source()` uses the optional PyMuPDF
parser when it is installed to extract page text. URL snapshots use
`capture_url_source()` with stdlib HTML text extraction.

## Current Pipeline

| Step | Owner | Output |
| --- | --- | --- |
| Capture event | worker `capture-source` / `capture_source()` | First journal `run` event with `workflow: capture_source`, before durable content is written. |
| DOI staging | `stage_catalog_source()` via worker `capture-source` | Writes an unchecked SQLite catalog row and durable blobs under `.memoria/blobs/source-content/<source_id>/`; no `source.md` or `references.bib` is written before enrichment. |
| DOI enrichment | `enrich_source()` via worker `enrich-source` | Requires Crossref, OpenAlex, Unpaywall, and full text for DOI records, caches raw provider JSON under `.memoria/blobs/provider-payloads/`, fetches provider-discovered open-access text only when the operation manifest allows that URL, merges canonical CSL-JSON, external IDs, field provenance, first-order Work graph edges, and `work_aspects` read-model rows, blocks with attention when full text is absent, then checks the catalog row, emits unchecked discovery candidate attention items, and materializes `references.bib`. |
| Raw copy | `capture_source()` / `stage_catalog_source()` | Writes `.memoria/blobs/source-content/<source_id>/raw/<filename>` plus `raw_text_sha256`. Raw blobs are gitignored and synced out of band. |
| Extracted content | `capture_source()` / `stage_catalog_source()` | Writes `.memoria/blobs/source-content/<source_id>/content.txt` plus `normalized_text_sha256`. Structured CSL aspects and explicit full-text sections populate the `work_aspects` read model. |
| BibTeX import | `memoria work import --format bibtex` / worker `capture-bibtex-source` | Parses one local BibTeX entry into a DOI/URL-derived `source_id` when available, citekey alias, CSL-JSON-shaped metadata, identifiers, durable raw `.bib` blob, and an unchecked SQLite catalog row. DOI imports queue `enrich-source`; no source/entity markdown or `references.bib` is written at import time. |
| CSL import | `memoria work import --format csl` / worker `capture-source` | Parses one local CSL-JSON item into a stable `source_id`, CSL-JSON-shaped metadata, identifiers, durable raw `.csl.json` blob, and an unchecked SQLite catalog row. DOI imports queue `enrich-source`; no source/entity markdown or `references.bib` update runs at import time. |
| URL snapshot | `stage_url_source()` / worker `capture-url-source` | Fetches one URL, preserves raw HTML, extracts plain text with stdlib `HTMLParser`, and writes an unchecked catalog row plus source-content blobs. |
| PDF import | `stage_pdf_source()` / worker `capture-pdf-source` | Parses raw PDF bytes into page-headed text behind a basic text-coherence guard and writes an unchecked catalog row plus source-content blobs. |
| Metadata merge | `capture_source()` / `enrich_source()` | Recapturing or enriching the same stable `source_id` merges non-empty identifiers, CSL-JSON fields, metadata status, and link lists instead of dropping previously captured source metadata. |
| Metadata-derived entities | `capture_source()` / `enrich_source()` | Records deterministic person, venue, organization, and source graph rows from CSL/OpenAlex metadata; exact duplicate checks read these rows. |
| Metadata check | `check_source_metadata()` / worker `check-source-metadata` | Flags checked sources that lack citekey, CSL-JSON basics, issued year, an external resource/identifier, carry conflicting DOI metadata, share an exact source external ID with another catalog row, hit the deterministic title/year/first-author duplicate block, or expose duplicate person ORCID/OpenAlex IDs or entity-name blocks. Active record-linkage findings emit stable `inbox/` work prompts for PI review; the operation never merges records. |
| Provider policy | `.memoria/config/providers.yaml` | Declares required DOI providers, endpoint templates, timeouts, and contact-email environment variables. The operation manifest allowlist must agree with enabled provider base URLs. |
| Catalog source row | catalog state | Source metadata lives in `.memoria/memoria.sqlite` with a mirror concept id of `catalog/sources/<source_id>` and DB/read-API `check_status`. There is no alpha.15 `source` frontmatter schema. |
| SQLite catalog row | `memoria_vault.runtime.state` | Writes staged or checked source metadata, enrichment runs, provider payload paths, external IDs, field provenance, and first-order Work graph edges in `.memoria/memoria.sqlite`, the catalog working-state source of truth. |
| Bibliography projection | `write_references_bib()` / worker projection refresh | Regenerates `references.bib` from checked SQLite catalog rows. Enrichment materializes it in the same worker commit after required providers pass; `check_references_bib()` checks this file, and `check_tracked_projections()` covers it with the rest of the tracked projection set. |
| Commit | trusted writer / projection writer | Capture writes SQLite state and gitignored blobs. DOI capture writes unchecked state only; enrichment and explicit projection refreshes commit required tracked projections such as `references.bib`. Raw and provider blobs stay out of git. |

The current extraction input is already-normalized markdown text, one DOI
payload staged for enrichment, one local BibTeX entry plus caller-supplied
content, one CSL-JSON item file, one URL snapshot, or PDF bytes when the
optional PyMuPDF parser is installed. ISBN metadata can arrive through portable
BibTeX/CSL imports, but alpha.15 has no standalone `work add --isbn` enrichment
route. Live URL smoke beyond mocked fetch tests, ISBN URL-depth enrichment,
ambiguous entity disambiguation, ambiguous identity flags, parser selection, and
richer coherence gates remain follow-on work.

## Catalog Source Record

Alpha.15 has no `source` frontmatter type. Source identity and verdict state live
in SQLite catalog rows and read-API responses:

| Field | Source |
| --- | --- |
| `source_id`, `title`, `description` | Required catalog identity fields. |
| `check_status` | DB/read-API verdict; never Concept frontmatter. |
| `resource`, `citekey`, `item_type`, `identifiers`, `csl_json`, `provider_coverage` | Metadata supplied by capture or enrichment. |
| `text_status` | `full-text`, `abstract-only`, or `metadata-only`; only `full-text` can produce a checked digest. |
| `raw_copy_path`, `content_path` | Relative paths to the raw blob and extracted markdown. |
| `raw_text_sha256`, `normalized_text_sha256` | Content hashes used by trace and later integrity checks. |

The `source_id` is the stable Work identifier. Citekeys are aliases and may be
corrected without renaming the Work; `memoria work update` refreshes the SQLite
catalog row before `references.bib` is rendered.

## Read Barrier

The captured source enters search/retrieval only after the DB/read API reports
`check_status = checked`.
Unchecked staged catalog rows, provider payloads, source-content blobs,
quarantined files, and raw blobs are not indexed by the checked-only search
input rebuild.

## Deferred Work

- ISBN URL-depth enrichment.
- Live URL smoke beyond mocked single-page fetch tests.
- PubMed, arXiv, broad source-discovery search, and UI.
- Parser selection and richer coherence gates for PDFs and other source formats.
- Ambiguous entity disambiguation beyond exact deterministic CSL author and venue paths.

## Related

- Catalog source record fields: [Frontmatter fields](frontmatter.md)
- DOI enrichment gate decision: [DOI catalog enrichment gates checked source promotion](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)
- Folder homes and skeleton: [Memoria configuration](configuration.md)
- Checked-only retrieval: [Search](search.md)
- Trusted writer and journal behavior: [System actions](system-actions.md)
