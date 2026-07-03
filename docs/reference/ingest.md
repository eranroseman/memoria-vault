---
title: Ingest routing
parent: Pipelines and I/O
grand_parent: Reference
---

# Ingest routing

Worker capture starts the catalog record, but scholarly identifiers do not
become checked source Concepts before provider verification. Worker
`capture-source` stages DOI/ISBN inputs as unchecked SQLite catalog rows plus
durable content/raw blobs under `.memoria/blobs/source-content/`; worker
`enrich-source` resolves required DOI providers, records provenance, and checks
the row only when provider and retraction checks pass.

The runtime helper `memoria_vault.runtime.capture.capture_source()` handles
already-supplied non-enrichment source payloads: it records a capture run,
writes the raw blob and extracted markdown, creates a `source` Concept plus
deterministic metadata-derived `person`/`venue` Concepts through the trusted
writer, promotes them checked, writes the checked source metadata into the
SQLite catalog state, and commits the Concepts, `content.md`, journal, and any
required `references.bib` projection together. Portable BibTeX/CSL imports use
the unchecked SQLite staging path instead of the checked source-Concept path.
The PDF adapter `capture_pdf_source()` uses the optional PyMuPDF parser when it
is installed to extract page text. URL snapshots use `capture_url_source()` with
stdlib HTML text extraction.

The older paper-ingest operation has been ported into
`memoria_vault.runtime.subsystems.processing.ingest`. The runtime package is the
source of truth for catalog writes.

## Current Pipeline

| Step | Owner | Output |
| --- | --- | --- |
| Capture event | worker `capture-source` / `capture_source()` | First journal `run` event with `workflow: capture_source`, before durable content is written. |
| DOI/ISBN staging | `stage_catalog_source()` via worker `capture-source` | Writes an unchecked SQLite catalog row and durable blobs under `.memoria/blobs/source-content/<source_id>/`; no `source.md` or `references.bib` is written before enrichment. |
| DOI enrichment | `enrich_source()` via worker `enrich-source` | Requires Crossref, OpenAlex, Unpaywall, and full text for DOI records, caches raw provider JSON under `.memoria/blobs/provider-payloads/`, fetches provider-discovered open-access text only when the operation manifest allows that URL, merges canonical CSL-JSON, external IDs, field provenance, and first-order Work graph edges, blocks with attention when full text is absent, then checks the catalog row, emits unchecked discovery candidate attention cards, and materializes `references.bib`. |
| Raw copy | `capture_source()` / `stage_catalog_source()` | Non-enrichment captures write `catalog/sources/<source_id>/raw/<filename>` plus `raw_text_sha256`; DOI/ISBN staging writes equivalent raw blobs under `.memoria/blobs/source-content/<source_id>/`. Raw blobs are gitignored and synced out of band. |
| Extracted content | `capture_source()` / `stage_catalog_source()` | Non-enrichment captures write `catalog/sources/<source_id>/content.md`; DOI/ISBN staging writes `.memoria/blobs/source-content/<source_id>/content.md`, both with `normalized_text_sha256`. |
| BibTeX import | `memoria work import --format bibtex` / worker `capture-bibtex-source` | Parses one local BibTeX entry into a DOI/URL-derived `source_id` when available, citekey alias, CSL-JSON-shaped metadata, identifiers, durable raw `.bib` blob, and an unchecked SQLite catalog row. DOI imports queue `enrich-source`; no source/entity markdown or `references.bib` is written at import time. |
| CSL import | `memoria work import --format csl` / worker `capture-source` | Parses one local CSL-JSON item into a stable `source_id`, CSL-JSON-shaped metadata, identifiers, durable raw `.csl.json` blob, and an unchecked SQLite catalog row. DOI imports queue `enrich-source`; no source/entity markdown or `references.bib` update runs at import time. |
| URL snapshot | `capture_url_source()` / worker `capture-url-source` | Fetches one URL, preserves raw HTML, extracts plain text with stdlib `HTMLParser`, and writes the same checked source Concept path. |
| PDF import | `capture_pdf_source()` / worker `capture-pdf-source` | Parses raw PDF bytes into page-headed markdown behind a basic text-coherence guard and writes the same checked source Concept path. |
| Metadata merge | `capture_source()` / `enrich_source()` | Recapturing or enriching the same stable source path merges non-empty identifiers, CSL-JSON fields, metadata status, and link lists instead of dropping previously captured source metadata. |
| Metadata-derived entities | `capture_source()` | Creates checked `catalog/entities/person-*.md` Concepts from CSL authors and `catalog/entities/venue-*.md` from `container-title`, links the source to them, and merges exact deterministic entity paths by appending `links.sources`. |
| Metadata check | `check_source_metadata()` / worker `check-source-metadata` | Flags checked sources that lack citekey, CSL-JSON basics, issued year, an external resource/identifier, carry conflicting DOI metadata, share an exact source external ID with another catalog row, hit the deterministic title/year/first-author duplicate block, or expose duplicate person ORCID/OpenAlex IDs. Active record-linkage findings emit stable `inbox/` work prompts for PI review; the operation never merges records. |
| Provider policy | `.memoria/config/providers.yaml` | Declares required DOI providers, endpoint templates, timeouts, and contact-email environment variables. The operation manifest allowlist must agree with enabled provider base URLs. |
| Source Concept | trusted writer / catalog state | Non-enrichment captures still write `catalog/sources/<source_id>/source.md`, born `unchecked` in staging and promoted to `checked` only after schema/folder validation. DOI/ISBN MVP keeps the checked source in SQLite/catalog projections until source-note materialization is introduced. |
| SQLite catalog row | `memoria_vault.runtime.state` | Writes staged or checked source metadata, enrichment runs, provider payload paths, external IDs, field provenance, and first-order Work graph edges in `.memoria/memoria.sqlite`, the catalog working-state source of truth. |
| Bibliography projection | `write_references_bib()` / worker projection refresh | Regenerates `references.bib` from checked SQLite catalog rows, falling back to checked source Concepts only when no SQLite catalog rows exist. Enrichment materializes it in the same worker commit after required providers pass; `check_references_bib()` checks this file, and `check_tracked_projections()` covers it with the rest of the tracked projection set. |
| Commit | trusted writer / projection writer | Non-enrichment captures commit `source.md`, `content.md`, `journal/<machine>.jsonl`, and required `references.bib`; DOI/ISBN capture writes unchecked state only, and enrichment commits journal plus required `references.bib`. Raw and provider blobs stay out of git. |

The current extraction input is already-normalized markdown text, one DOI/ISBN
payload staged for enrichment, one local BibTeX entry plus caller-supplied
content, one CSL-JSON item file, one URL snapshot, or PDF bytes when the
optional PyMuPDF parser is installed. Live URL smoke beyond mocked fetch tests,
ISBN URL-depth enrichment, ambiguous entity disambiguation, ambiguous identity
flags, parser selection, and richer coherence gates remain follow-on work.

## Source Concept

`source.md` uses the schema-owned `source` type:

| Field | Source |
| --- | --- |
| `type`, `check_status`, `title`, `description`, `source_id` | Required source schema fields. |
| `resource`, `citekey`, `item_type`, `identifiers`, `csl_json`, `provider_coverage` | Optional metadata supplied by the capture caller. |
| `text_status` | `full-text`, `abstract-only`, or `metadata-only`; only `full-text` can produce a checked digest. |
| `raw_copy_path`, `content_path` | Relative paths to the raw blob and extracted markdown. |
| `raw_text_sha256`, `normalized_text_sha256` | Content hashes used by trace and later integrity checks. |

The `source_id` is the stable path identifier. Citekeys are aliases and may be
corrected without renaming the Concept; marking the edited source checked
refreshes the SQLite catalog row before `references.bib` is rendered.

## Read Barrier

The captured source enters qmd/retrieval only after the DB/read API reports
`check_status = checked`.
Unchecked staged catalog rows, provider payloads, source-content blobs,
quarantined files, and raw blobs are not indexed by the checked-only search
input rebuild.

## Deferred Work

- ISBN URL-depth enrichment.
- Live URL smoke beyond mocked single-page fetch tests.
- Semantic Scholar, PubMed, arXiv, and UI.
- Parser selection and richer coherence gates for PDFs and other source formats.
- Ambiguous entity disambiguation beyond exact deterministic CSL author and venue paths.

## Related

- Source schema fields: [Frontmatter fields](frontmatter.md)
- DOI enrichment gate decision: [ADR-123](../adr/123-doi-catalog-enrichment-gate.md)
- Folder homes and skeleton: [Memoria configuration](configuration.md)
- Checked-only retrieval: [Search](search.md)
- Trusted writer and journal behavior: [System actions](system-actions.md)
