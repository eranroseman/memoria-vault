---
title: Capture and ingest a source
parent: Library
grand_parent: How-to guides
---

# Capture and ingest a source

Alpha.11 capture currently has the backend spine, not the final Obsidian
palette/plugin flow. The implemented path creates the catalog source record
under `catalog/sources/<source_id>/` and routes the source Concept through the
trusted writer.

**1. Capture the source content.**

Use the capture operation with a stable `source_id`, title, description, raw
bytes or raw text, and extracted markdown text. The direct helper is
`memoria_vault.runtime.capture.capture_source()`. The same trusted-writer path
also has adapters for one BibTeX entry, one Zotero Local API item JSON snapshot,
one Zotero local item key, one URL snapshot, and raw PDF bytes.

**2. Confirm the catalog files.**

The capture writes:

- `catalog/sources/<source_id>/source.md`
- `catalog/sources/<source_id>/content.md`
- `catalog/sources/<source_id>/raw/<filename>`

The `source.md` frontmatter includes `raw_copy_path`, `content_path`,
`raw_text_sha256`, and `normalized_text_sha256`.

**3. Confirm the trace.**

The journal has `run`, `derived`, and `check-fired` events. The git commit
contains `source.md`, `content.md`, and `journal/<machine>.jsonl`; raw blobs are
gitignored and synced out of band.

## Deferred UI

Live Zotero selection capture in Obsidian, live URL smoke beyond mocked fetch
tests, metadata lookup, entity
disambiguation/merge, and the Obsidian command-palette flow remain alpha.11
follow-on work.

## Related

- Pipeline details: [Ingest routing](../../reference/ingest.md)
- Source fields: [Frontmatter fields](../../reference/frontmatter.md)
- Trusted writer: [System actions](../../reference/system-actions.md)
