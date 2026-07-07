---
title: Capture and ingest a source
parent: Library
grand_parent: How-to guides
nav_order: 1
---

# Capture and ingest a source

Capture always enters through a SQLite worker request. DOI, BibTeX, CSL JSON,
URL, PDF, and local text imports create catalog Work rows under
`.memoria/memoria.sqlite` plus durable blobs under `.memoria/blobs/source-content/`.

**1. Capture a URL from the CLI.**

```bash
memoria work add --workspace <vault> --url https://example.test/source
```

The CLI writes one SQLite request for `capture-url-source`; the worker fetches,
normalizes, stores blobs, writes the catalog row, and journals the capture.

**2. Import portable bibliographic files.**

Use `memoria work import --format bibtex|csl --file <path>` for portable
metadata, including records that carry ISBN metadata. Imports write unchecked
Work rows and queue DOI enrichment when a DOI is present. They do not fetch from
a reference-manager API, create source/entity Markdown, or update
`bibliography.bib` at import time. There is no standalone `memoria work add
--isbn` route.

**3. Confirm the catalog row and blobs.**

Use JSON output or `memoria work export` to inspect the Work:

```bash
memoria work add --workspace <vault> --file paper.txt --title "Paper title" --json
memoria work export --workspace <vault> <work-id>
```

The output includes `check_status`, `text_status`, `content_path`, `raw_path`,
`normalized_text_sha256`, and `raw_text_sha256`. Paths are workspace-relative
and live under `.memoria/blobs/source-content/<work_id>/`.

**4. Confirm the trace.**

The journal has `run`, `derived`, and `check-fired` events. Source-content blobs
are gitignored; tracked projections such as `bibliography.bib` are committed only
when enrichment or projection refresh makes them current.

## Deferred UI

Reference-manager adapters are not part of the standalone runtime.

## Related

- Pipeline details: [Ingest routing](../../reference/ingest.md)
- Source record fields: [Ingest routing](../../reference/ingest.md)
- Trusted writer: [System actions](../../reference/system-actions.md)
