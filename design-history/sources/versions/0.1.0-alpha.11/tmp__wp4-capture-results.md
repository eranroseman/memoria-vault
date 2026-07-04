# WP4 Capture Slice Results

Timestamp: 2026-06-29T06:16:47Z

Scope: first WP4 implementation slice for catalog source capture:

- `capture_source()` records a capture `run` event before writing files;
- the worker exposes the same path as `capture-source`, preserving the
  source/content/journal commit boundary;
- raw bytes land under `catalog/sources/<source_id>/raw/` and are immutable
  once written;
- extracted markdown lands at `catalog/sources/<source_id>/content.md`;
- `catalog/sources/<source_id>/source.md` is created through the trusted
  writer, born in staging, promoted to `check_status: checked`, and traced with
  `derived` + `check-fired` events;
- the git commit contains `source.md`, `content.md`, and
  `journal/<machine>.jsonl`; raw blobs remain gitignored and are referenced by
  path + SHA-256;
- `capture_bibtex_source()` now parses one local BibTeX entry into a DOI/URL
  `source_id` when available, citekey alias, CSL-JSON-shaped metadata,
  identifiers, raw `.bib`, content, and the same checked source Concept path;
  the worker exposes this as
  `capture-bibtex-source`;
- `capture_zotero_source()` maps one Zotero Local API item JSON snapshot into a
  stable Zotero-key-based `source_id`, citekey alias, CSL-JSON-shaped metadata,
  identifiers, raw `.zotero.json`, content, and the same checked source Concept
  path; the worker exposes this as `capture-zotero-source`;
- `capture_zotero_local_source()` fetches one Zotero item key from the local
  desktop API with stdlib HTTP, then routes the returned JSON through the same
  snapshot adapter; the worker `capture-zotero-source` payload accepts either a
  `zotero_item` object or an `item_key`;
- `capture_url_source()` fetches one URL with stdlib HTTP, preserves the raw HTML
  snapshot, extracts plain text with stdlib `HTMLParser`, and writes the same
  checked source Concept path; the worker exposes this as `capture-url-source`;
- `capture_source()` now creates deterministic metadata-derived entity Concepts:
  `person` rows from CSL authors and `venue` rows from CSL `container-title`,
  links the checked source to them, and commits the source/content/entities with
  the journal in one trusted-writer commit;
- repeated deterministic entity paths merge the new source into the existing
  entity's `links.sources` instead of replacing prior source links;
- recapturing the same stable source path with identical raw/content now merges
  non-empty `identifiers`, CSL-JSON fields, metadata status, and link lists
  instead of dropping previously captured metadata;
- `capture_pdf_source()` uses the optional PyMuPDF parser path to extract
  page-headed markdown from raw PDF bytes and derive page/text/bbox
  `annotation_ref` selectors for requested quotes; the worker exposes this as
  `capture-pdf-source`;
- PDF capture rejects obvious broken parser output with a basic text-coherence
  guard before journaling or writing source files;
- PDF capture now preflights requested annotation quotes before any source write
  or journal event: missing quotes, ambiguous quote matches, and matched blocks
  without usable page bbox data fail closed without leaving partial catalog
  files;
- the worker `capture-pdf-source` operation inherits the same fail-closed
  selector boundary: a queued job with a missing annotation quote moves to
  `failed` without writing the source folder or journal rows;
- `render_references_bib()` / `write_references_bib()` regenerate
  `references.bib` from checked sources with citekeys, and
  `check_references_bib()` gives the drift check; the worker exposes this as
  `regenerate-references-bib`;
- `check_source_metadata()` flags checked sources whose bibliographic metadata
  lacks citekey, CSL-JSON basics, issued year, or an external
  resource/identifier; the worker exposes this as `check-source-metadata`;
- PDF capture contract tests use monkeypatched parser output to prove raw
  `.pdf` bytes are preserved and requested quote selectors derive `source_id`,
  `raw_copy_path`, page, text span, and bbox metadata against the checked
  source; incoherent parser text fails before journaling;
- Zotero capture tests prove one Local API item JSON snapshot preserves raw
  `.zotero.json`, citekey alias, DOI identifier/resource, CSL author/year
  metadata, content text, and the checked source path;
- mocked Local API tests prove item-key fetch URL construction, timeout
  handling, and worker dispatch without requiring a live Zotero process;
- worker-dispatched URL and Zotero Local API source-capture paths enforce the
  checked operation Concept's `allowed_network` before any fetch helper runs;
- a live Zotero Local API smoke on 2026-06-29 fetched one item key from
  `127.0.0.1:23119` into a disposable alpha.11 workspace through
  `capture_zotero_local_source()`: item fetch status was 200, the stable
  `catalog/sources/zotero-live-smoke/source.md` Concept was promoted to
  `check_status: checked`, raw `.zotero.json` was written, and the journal was
  committed; the smoke did not print library metadata or persist the disposable
  workspace. Zotero annotation import was removed from alpha.11 scope after the
  scope correction that Zotero is used only for item/source imports with no
  annotations;
- URL capture tests prove raw HTML is preserved, script/style content is skipped
  during text extraction, the checked source carries `item_type: webpage`, and
  the worker dispatches `capture-url-source`;
- a loopback HTTP smoke test starts a stdlib local server, runs
  `capture_url_source()` through the real URL fetch path, and verifies checked
  source, content, raw HTML, and journal events; the default command sandbox
  denies local sockets, so the same test skips there and passes with local-socket
  permission;
- entity capture tests prove BibTeX/Zotero metadata produces checked
  `catalog/entities/` Concepts, source `links` to those Concepts, and exact-path
  entity source-link merges;
- entity capture now preserves conflicting external identity evidence instead
  of silently merging it: when a reused person/venue entity receives a different
  external ID, the entity keeps the original ID, records the incoming conflict
  under `metadata.identity_conflicts`, and marks
  `metadata.identity_status: ambiguous`;
- recapture tests prove the stable source path merges identifiers, CSL-JSON, and
  metadata status without replacing previously captured source metadata;
- source identity tests prove an explicit stable `source_id` survives a PI
  citekey correction and `references.bib` follows the corrected citekey alias
  without renaming the source Concept path;
- current ingest docs now describe the alpha.11 catalog path instead of the
  retired `catalog/papers` / `notes/sources` flow.
- direct search/capture reference docs no longer claim the old QuickAdd/Tier
  paper-ingest path or unproven hybrid retrieval acceptance.

This is not the full WP4 pipeline. External URL smoke beyond the loopback/local
fetch test, larger real-corpus parser-quality measurement, live identifier
lookup, live entity disambiguation/adjudication, and live bibliographic
enrichment remain open WP4 work. Zotero remains an item/source import path only;
annotation import is not an alpha.11 capability or release gate.

Verification:

```bash
python -m pytest tests/test_capture.py tests/test_trusted_writer.py tests/test_worker_queue.py tests/test_search_index.py tests/test_qmd_filter_mcp.py
python -m ruff check src/memoria_vault/runtime/capture.py src/memoria_vault/runtime/trusted_writer.py src/memoria_vault/runtime/__init__.py tests/test_capture.py tests/test_trusted_writer.py tests/test_worker_queue.py
python -m ruff format --check src/memoria_vault/runtime/capture.py src/memoria_vault/runtime/trusted_writer.py src/memoria_vault/runtime/__init__.py tests/test_capture.py tests/test_trusted_writer.py tests/test_worker_queue.py
python scripts/docs_doctor.py docs
python scripts/agents_doctor.py --write
python scripts/agents_doctor.py
python -m pytest tests/test_capture.py tests/test_worker_queue.py
python -m ruff check src/memoria_vault/runtime/capture.py src/memoria_vault/runtime/worker.py tests/test_capture.py tests/test_worker_queue.py
python -m ruff format --check src/memoria_vault/runtime/capture.py src/memoria_vault/runtime/worker.py tests/test_capture.py tests/test_worker_queue.py
python -m pytest tests/test_integrity.py tests/test_worker_queue.py
python -m ruff check src/memoria_vault/runtime/capture.py src/memoria_vault/runtime/integrity.py src/memoria_vault/runtime/worker.py tests/test_capture.py tests/test_integrity.py tests/test_worker_queue.py
python -m ruff format --check src/memoria_vault/runtime/capture.py src/memoria_vault/runtime/integrity.py src/memoria_vault/runtime/worker.py tests/test_capture.py tests/test_integrity.py tests/test_worker_queue.py
python -m pytest tests/test_capture.py tests/test_worker_queue.py tests/test_capabilities.py -q
python -m pytest tests/test_worker_queue.py::test_worker_runs_capture_url_source_operation_jobs tests/test_worker_queue.py::test_worker_rejects_capture_url_source_outside_allowed_network tests/test_worker_queue.py::test_worker_runs_capture_zotero_source_from_local_api_key tests/test_operations.py -q
python -m ruff check src/memoria_vault/runtime/capture.py src/memoria_vault/runtime/worker.py tests/test_capture.py tests/test_worker_queue.py tests/test_capabilities.py
python -m ruff format --check src/memoria_vault/runtime/capture.py src/memoria_vault/runtime/worker.py tests/test_capture.py tests/test_worker_queue.py tests/test_capabilities.py
python -m pytest tests/test_capture.py::test_capture_url_source_fetches_from_loopback_http_server -q
python -m pytest tests/test_capture.py -q
python -m pytest tests/test_capture.py tests/test_worker_queue.py::test_worker_runs_capture_pdf_source_operation_jobs tests/test_worker_queue.py::test_worker_capture_pdf_source_fails_before_partial_write -q
python -m pytest tests/test_capture.py tests/test_integrity.py -q
python -m ruff check src/memoria_vault/runtime/capture.py tests/test_capture.py
python -m ruff check src/memoria_vault/runtime/capture.py tests/test_capture.py tests/test_worker_queue.py
python -m ruff check src/memoria_vault/runtime/capture.py src/memoria_vault/runtime/integrity.py tests/test_capture.py tests/test_integrity.py
python -m ruff format --check src/memoria_vault/runtime/capture.py tests/test_capture.py tests/test_worker_queue.py
python -m ruff format --check src/memoria_vault/runtime/capture.py src/memoria_vault/runtime/integrity.py tests/test_capture.py tests/test_integrity.py
```

Result: all passed.

## PDF parser-backed proof status

Timestamp: 2026-06-29T12:10:21Z

The Memoria-test runtime venv has `fitz` and `pymupdf4llm` installed. The
start-blocker verifier ran a parser-backed tiny PDF fixture through
`capture_pdf_source()` and proved page-headed content plus quote/page/bbox
selector derivation against real PDF bytes. This closes the local parser-backed
fixture proof; it does not replace larger real-corpus parser-quality
evaluation.

Verification:

```bash
/home/eranr/Memoria-test/.memoria/.venv/bin/python docs/releasing/0.1.0-alpha.11/tmp/verify_start_blockers.py
```

Result: verifier remains `PARTIAL` overall because Obsidian visual/attended
activation is still open, but the PDF row passed:
`fitz=True`, `content_has_page=True`, `quote_found=True`, `page=1`, and
`bbox=[72.0, 60.17, 294.55, 75.29]`.
