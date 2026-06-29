---
title: Ingest routing
parent: Pipelines and I/O
grand_parent: Reference
---

# Ingest routing

Alpha.11 capture starts the catalog record. The core helper is
`memoria_vault.runtime.capture.capture_source()`: it records a capture run,
writes the raw blob and extracted markdown, creates a `source` Concept plus
deterministic metadata-derived `person`/`venue` Concepts through the trusted
writer, promotes them checked, and commits the Concepts, `content.md`, and
journal together. The local BibTeX adapter
`capture_bibtex_source()` maps one BibTeX entry into that same path. The Zotero
adapters map either one Zotero Local API item JSON snapshot
(`capture_zotero_source()`) or fetch one item key from the local desktop API
first (`capture_zotero_local_source()`). Zotero imports are source/item imports
only in alpha.11; Zotero annotations are not imported. The PDF
adapter `capture_pdf_source()` uses the optional PyMuPDF parser from the vault
MCP requirements to extract page text. URL snapshots use `capture_url_source()`
with stdlib HTML text extraction.

The older paper-ingest operation under
`vault-template/.memoria/operations/processing/ingest/` is pre-reset code. It is
not the alpha.11 source of truth for catalog writes.

## Current Pipeline

| Step | Owner | Output |
| --- | --- | --- |
| Capture event | `capture_source()` | First journal `run` event with `workflow: capture_source`, before files are written. |
| Raw copy | `capture_source()` | `catalog/sources/<source_id>/raw/<filename>` plus `raw_text_sha256`. Raw blobs are gitignored and synced out of band. |
| Extracted content | `capture_source()` | `catalog/sources/<source_id>/content.md` plus `normalized_text_sha256`. |
| BibTeX import | `capture_bibtex_source()` | Parses one local BibTeX entry into a DOI/URL-derived `source_id` when available, citekey alias, CSL-JSON-shaped metadata, identifiers, raw `.bib`, and the same checked source Concept. |
| Zotero item import | `capture_zotero_source()` / `capture_zotero_local_source()` / worker `capture-zotero-source` | Maps one Zotero Local API item JSON snapshot or fetches one local API item key, then writes stable `source_id`, citekey alias, CSL-JSON-shaped metadata, identifiers, raw `.zotero.json`, and the same checked source Concept. |
| URL snapshot | `capture_url_source()` / worker `capture-url-source` | Fetches one URL, preserves raw HTML, extracts plain text with stdlib `HTMLParser`, and writes the same checked source Concept path. |
| PDF import | `capture_pdf_source()` / worker `capture-pdf-source` | Parses raw PDF bytes into page-headed markdown behind a basic text-coherence guard and writes the same checked source Concept path. |
| Metadata merge | `capture_source()` | Recapturing the same stable source path with identical raw/content merges non-empty identifiers, CSL-JSON fields, metadata status, and link lists instead of dropping previously captured source metadata. |
| Metadata-derived entities | `capture_source()` | Creates checked `catalog/entities/person-*.md` Concepts from CSL authors and `catalog/entities/venue-*.md` from `container-title`, links the source to them, and merges exact deterministic entity paths by appending `links.sources`. |
| Metadata check | `check_source_metadata()` / worker `check-source-metadata` | Flags checked sources that lack citekey, CSL-JSON basics, issued year, an external resource/identifier, or carry conflicting DOI metadata. |
| Source Concept | trusted writer | `catalog/sources/<source_id>/source.md`, born `unchecked` in staging and promoted to `checked` only after schema/folder validation. |
| Bibliography projection | `write_references_bib()` / worker projection refresh | Regenerates `references.bib` from checked source Concepts with citekeys; `check_references_bib()` checks this file, and `check_tracked_projections()` covers it with the rest of the tracked projection set. |
| Commit | trusted writer | One git commit for `source.md`, `content.md`, and `journal/<machine>.jsonl`; raw stays out of git. |

The current extraction input is already-normalized markdown text, one local
BibTeX entry plus caller-supplied content, one Zotero Local API item JSON
snapshot or item key, one URL snapshot, or PDF bytes when the optional PyMuPDF
parser is installed. Live Zotero availability smoke, live URL smoke beyond
mocked fetch tests, live identifier lookup, ambiguous entity disambiguation,
ambiguous identity flags, parser selection, and richer coherence gates remain
WP4 follow-on work.

## Source Concept

`source.md` uses the schema-owned `source` type:

| Field | Source |
| --- | --- |
| `type`, `check_status`, `title`, `description`, `source_id` | Required source schema fields. |
| `resource`, `citekey`, `item_type`, `identifiers`, `csl_json`, `metadata_status` | Optional metadata supplied by the capture caller. |
| `raw_copy_path`, `content_path` | Relative paths to the raw blob and extracted markdown. |
| `raw_text_sha256`, `normalized_text_sha256` | Content hashes used by trace and later integrity checks. |

The `source_id` is the stable path identifier. Citekeys are aliases and may be
corrected without renaming the Concept.

## Read Barrier

The captured `source` enters qmd/retrieval only after promotion sets
`check_status: checked`. Unchecked staging files, quarantined files, and raw
blobs are not indexed by the checked-only search input rebuild.

## Deferred Work

- Live capture adapters: identifier lookup.
- Live URL smoke beyond mocked single-page fetch tests.
- Live Zotero availability smoke beyond mocked item-key fetch tests.
- Parser selection and richer coherence gates for PDFs and other source formats.
- Zotero annotation import and PDF quote/bbox annotation references.
- Ambiguous entity disambiguation beyond exact deterministic CSL author and venue paths.

## Related

- Source schema fields: [Frontmatter fields](frontmatter.md)
- Folder homes and skeleton: [Memoria configuration](configuration.md)
- Checked-only retrieval: [Search](search.md)
- Trusted writer and journal behavior: [System actions](system-actions.md)
