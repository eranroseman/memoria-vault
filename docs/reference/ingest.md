---
title: Ingest routing
parent: Pipelines and I/O
grand_parent: Reference
---

# Ingest routing

Alpha.13 capture starts the catalog record, but scholarly identifiers no longer
become checked source Concepts before provider verification. Worker
`capture-source` stages DOI/ISBN inputs as unchecked SQLite catalog rows plus
durable content/raw blobs under `.memoria/blobs/source-content/`; worker
`enrich-source` resolves required DOI providers, records provenance, and checks
the row only when provider and retraction checks pass.

The legacy direct helper `memoria_vault.runtime.capture.capture_source()` still
handles already-supplied non-enrichment source payloads: it records a capture
run, writes the raw blob and extracted markdown, creates a `source` Concept plus
deterministic metadata-derived `person`/`venue` Concepts through the trusted
writer, promotes them checked, writes the checked source metadata into the
SQLite catalog state, and commits the Concepts, `content.md`, journal, and any
required `references.bib` projection together. The local BibTeX adapter
`capture_bibtex_source()` maps one BibTeX entry into that path. The Zotero
adapters map either one Zotero Local API item JSON snapshot
(`capture_zotero_source()`) or fetch one item key from the local desktop API
first (`capture_zotero_local_source()`). Zotero imports are source/item imports
only in alpha.13; Zotero annotations are not imported. The PDF adapter
`capture_pdf_source()` uses the optional PyMuPDF parser from the vault MCP
requirements to extract page text. URL snapshots use `capture_url_source()`
with stdlib HTML text extraction.

The older paper-ingest operation under
`vault-template/.memoria/operations/processing/ingest/` is pre-reset code. It is
not the alpha.13 source of truth for catalog writes.

## Current Pipeline

| Step | Owner | Output |
| --- | --- | --- |
| Capture event | worker `capture-source` / `capture_source()` | First journal `run` event with `workflow: capture_source`, before durable content is written. |
| DOI/ISBN staging | `stage_catalog_source()` via worker `capture-source` | Writes an unchecked SQLite catalog row and durable blobs under `.memoria/blobs/source-content/<source_id>/`; no `source.md` or `references.bib` is written before enrichment. |
| DOI enrichment | `enrich_source()` via worker `enrich-source` | Requires Crossref, OpenAlex, Unpaywall, and full text for DOI records, caches raw provider JSON under `.memoria/blobs/provider-payloads/`, fetches provider-discovered open-access text only when the operation manifest allows that URL, merges canonical CSL-JSON, external IDs, field provenance, and first-order Work graph edges, blocks with attention when full text is absent, then checks the catalog row, emits unchecked discovery candidate attention cards, and materializes `references.bib`. |
| Raw copy | `capture_source()` / `stage_catalog_source()` | Non-enrichment captures write `catalog/sources/<source_id>/raw/<filename>` plus `raw_text_sha256`; DOI/ISBN staging writes equivalent raw blobs under `.memoria/blobs/source-content/<source_id>/`. Raw blobs are gitignored and synced out of band. |
| Extracted content | `capture_source()` / `stage_catalog_source()` | Non-enrichment captures write `catalog/sources/<source_id>/content.md`; DOI/ISBN staging writes `.memoria/blobs/source-content/<source_id>/content.md`, both with `normalized_text_sha256`. |
| BibTeX import | `capture_bibtex_source()` | Parses one local BibTeX entry into a DOI/URL-derived `source_id` when available, citekey alias, CSL-JSON-shaped metadata, identifiers, raw `.bib`, and the same checked source Concept. |
| Zotero item import | `capture_zotero_source()` / `capture_zotero_local_source()` / worker `capture-zotero-source` | Maps one Zotero Local API item JSON snapshot or fetches one local API item key, then writes stable `source_id`, citekey alias, CSL-JSON-shaped metadata, identifiers, raw `.zotero.json`, and the same checked source Concept. |
| URL snapshot | `capture_url_source()` / worker `capture-url-source` | Fetches one URL, preserves raw HTML, extracts plain text with stdlib `HTMLParser`, and writes the same checked source Concept path. |
| PDF import | `capture_pdf_source()` / worker `capture-pdf-source` | Parses raw PDF bytes into page-headed markdown behind a basic text-coherence guard and writes the same checked source Concept path. |
| Metadata merge | `capture_source()` / `enrich_source()` | Recapturing or enriching the same stable source path merges non-empty identifiers, CSL-JSON fields, metadata status, and link lists instead of dropping previously captured source metadata. |
| Metadata-derived entities | `capture_source()` | Creates checked `catalog/entities/person-*.md` Concepts from CSL authors and `catalog/entities/venue-*.md` from `container-title`, links the source to them, and merges exact deterministic entity paths by appending `links.sources`. |
| Metadata check | `check_source_metadata()` / worker `check-source-metadata` | Flags checked sources that lack citekey, CSL-JSON basics, issued year, an external resource/identifier, or carry conflicting DOI metadata. |
| Provider policy | `.memoria/config/providers.yaml` | Declares required DOI providers, endpoint templates, timeouts, and contact-email environment variables. The operation manifest allowlist must agree with enabled provider base URLs. |
| Source Concept | trusted writer / catalog state | Non-enrichment captures still write `catalog/sources/<source_id>/source.md`, born `unchecked` in staging and promoted to `checked` only after schema/folder validation. DOI/ISBN MVP keeps the checked source in SQLite/catalog projections until source-note materialization is introduced. |
| SQLite catalog row | `memoria_vault.runtime.state` | Writes staged or checked source metadata, enrichment runs, provider payload paths, external IDs, field provenance, and first-order Work graph edges in `.memoria/memoria.sqlite`, the catalog working-state source of truth. |
| Bibliography projection | `write_references_bib()` / worker projection refresh | Regenerates `references.bib` from checked SQLite catalog rows, falling back to checked source Concepts only when no SQLite catalog rows exist. Enrichment materializes it in the same worker commit after required providers pass; `check_references_bib()` checks this file, and `check_tracked_projections()` covers it with the rest of the tracked projection set. |
| Commit | trusted writer / projection writer | Non-enrichment captures commit `source.md`, `content.md`, `journal/<machine>.jsonl`, and required `references.bib`; DOI/ISBN capture writes unchecked state only, and enrichment commits journal plus required `references.bib`. Raw and provider blobs stay out of git. |

The current extraction input is already-normalized markdown text, one DOI/ISBN
payload staged for enrichment, one local BibTeX entry plus caller-supplied
content, one Zotero Local API item JSON snapshot or item key, one URL snapshot,
or PDF bytes when the optional PyMuPDF parser is installed. Live Zotero
availability smoke, live URL smoke beyond mocked fetch tests, ISBN URL-depth
enrichment, ambiguous entity disambiguation, ambiguous identity flags, parser
selection, and richer coherence gates remain follow-on work.

## Source Concept

`source.md` uses the schema-owned `source` type:

| Field | Source |
| --- | --- |
| `type`, `check_status`, `title`, `description`, `source_id` | Required source schema fields. |
| `resource`, `citekey`, `item_type`, `identifiers`, `csl_json`, `metadata_status` | Optional metadata supplied by the capture caller. |
| `text_status` | `full-text`, `abstract-only`, or `metadata-only`; only `full-text` can produce a checked digest. |
| `raw_copy_path`, `content_path` | Relative paths to the raw blob and extracted markdown. |
| `raw_text_sha256`, `normalized_text_sha256` | Content hashes used by trace and later integrity checks. |

The `source_id` is the stable path identifier. Citekeys are aliases and may be
corrected without renaming the Concept; marking the edited source checked
refreshes the SQLite catalog row before `references.bib` is rendered.

## Read Barrier

The captured source enters qmd/retrieval only after `check_status: checked`.
Unchecked staged catalog rows, provider payloads, source-content blobs,
quarantined files, and raw blobs are not indexed by the checked-only search
input rebuild.

## Deferred Work

- ISBN URL-depth enrichment.
- Live URL smoke beyond mocked single-page fetch tests.
- Live Zotero availability smoke beyond mocked item-key fetch tests.
- Semantic Scholar, PubMed, arXiv, graph enrichment, embeddings, and UI.
- Parser selection and richer coherence gates for PDFs and other source formats.
- Zotero annotation import and PDF quote/bbox annotation references.
- Ambiguous entity disambiguation beyond exact deterministic CSL author and venue paths.

## Related

- Source schema fields: [Frontmatter fields](frontmatter.md)
- DOI enrichment gate decision: [ADR-123](../adr/123-doi-catalog-enrichment-gate.md)
- Folder homes and skeleton: [Memoria configuration](configuration.md)
- Checked-only retrieval: [Search](search.md)
- Trusted writer and journal behavior: [System actions](system-actions.md)
