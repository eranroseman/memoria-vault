---
title: Capture and ingest a source
parent: Library
grand_parent: How-to guides
---

# Capture and ingest a source

Alpha.11 capture creates a checked source Concept under
`catalog/sources/<source_id>/` through the worker/trusted-writer path. The
Inspector ships a URL capture control; the same backend also supports direct
BibTeX, Zotero-item, local item-key, PDF, and raw-content helpers.

**1. Queue URL capture from Obsidian when you have a URL.**

Open Memoria Inspector, paste the URL into **Source URL**, then click
**Capture URL**. The plugin writes one `capture-url-source` job to
`.memoria/queue/pending/`; the worker fetches, normalizes, checks, commits, and
journals the source.

**2. Use backend capture helpers for non-URL inputs.**

For scripts or tests, call the capture operation with a stable `source_id`,
title, description, raw bytes or raw text, and extracted markdown text. The
direct helper is `memoria_vault.runtime.capture.capture_source()`. Adapters
exist for one BibTeX entry, one Zotero Local API item JSON snapshot, one Zotero
local item key, one URL snapshot, and raw PDF bytes.

**3. Confirm the catalog files.**

The capture writes:

- `catalog/sources/<source_id>/source.md`
- `catalog/sources/<source_id>/content.md`
- `catalog/sources/<source_id>/raw/<filename>`

The `source.md` frontmatter includes `raw_copy_path`, `content_path`,
`raw_text_sha256`, and `normalized_text_sha256`.

**4. Confirm the trace.**

The journal has `run`, `derived`, and `check-fired` events. The git commit
contains `source.md`, `content.md`, and `journal/<machine>.jsonl`; raw blobs are
gitignored and synced out of band.

## Deferred UI

Live Zotero selection capture in Obsidian remains follow-on work. Alpha.11
assumes Zotero is used for imports only; annotation import is deferred.

## Related

- Pipeline details: [Ingest routing](../../reference/ingest.md)
- Source fields: [Frontmatter fields](../../reference/frontmatter.md)
- Trusted writer: [System actions](../../reference/system-actions.md)
