---
title: Capture and ingest a source
parent: Library
grand_parent: How-to guides
---

# Capture and ingest a source

Capture always enters through a SQLite worker request. DOI/ISBN, BibTeX, and CSL
JSON imports stage unchecked catalog Work rows under
`.memoria/memoria.sqlite` plus durable blobs under `.memoria/blobs/source-content/`.
URL, PDF, and already-supplied non-enrichment text can still produce checked
source Concepts after the worker checks them.

**1. Capture a URL from the CLI.**

```bash
memoria work capture --workspace <vault> --url https://example.test/source
```

The CLI writes one SQLite request for `capture-url-source`; the worker fetches,
normalizes, checks, commits, and journals the source.

**2. Import portable bibliographic files.**

Use `memoria work import --format bibtex|csl --file <path>` for portable
metadata. Imports write unchecked Work rows and queue DOI enrichment when a DOI
is present. They do not fetch from a reference-manager API, create source/entity
Markdown, or update `references.bib` at import time.

**3. Confirm checked source files, when the route creates them.**

Checked non-enrichment captures write:

- `catalog/sources/<source_id>/source.md`
- `catalog/sources/<source_id>/content.md`
- `catalog/sources/<source_id>/raw/<filename>`

The `source.md` frontmatter includes `raw_copy_path`, `content_path`,
`raw_text_sha256`, and `normalized_text_sha256`.

For staged Work imports, confirm the row in `.memoria/memoria.sqlite` and the
blob paths under `.memoria/blobs/source-content/<source_id>/`.

**4. Confirm the trace.**

The journal has `run`, `derived`, and `check-fired` events. The git commit
contains `source.md`, `content.md`, and `journal/<machine>.jsonl`; raw blobs are
gitignored and synced out of band.

## Deferred UI

Reference-manager adapters are not part of the standalone alpha.14 runtime.

## Related

- Pipeline details: [Ingest routing](../../reference/ingest.md)
- Source fields: [Frontmatter fields](../../reference/frontmatter.md)
- Trusted writer: [System actions](../../reference/system-actions.md)
