# WP-Docs Alpha.10 Surface Retirement Results

Timestamp: 2026-06-29T03:10:00Z

Scope: documentation and shipped-skeleton cleanup after the alpha.11 schema and
QuickAdd reset:

- removed the alpha.10 Mediterranean sample bundle from the fresh skeleton and
  installer manifest; no `.memoria/samples` directories are created;
- kept the sample-vault docs path as a retired reference instead of a runnable
  how-to;
- retired tutorial pages and alpha.10 how-to workflows that depended on deleted
  QuickAdd commands, old `notes/*` homes, or candidate/gap card Concepts;
- retired the runtime schema-migration how-to and links to it; alpha.11 has no
  migration, upgrade, or backwards-compatibility workflow for an installed
  vault;
- updated section indexes so retired pages are labeled historical;
- updated Portals to browse alpha.11 folder homes and refreshed the plugin
  provenance digest.

This does not implement the remaining live/runtime alpha.11 evidence. Later
same-day evidence supersedes the old live-availability gaps for Zotero item-list
reachability, Obsidian Local REST command execution, and the deterministic G3
worker cycle. Still open: visual
Obsidian panel rendering by screenshot/human inspection, the attended
`Memoria-test` product cycle, and the full seeded-error release verdict.

Verification:

```bash
python scripts/docs_doctor.py docs
python scripts/agents_doctor.py
python scripts/status_doctor.py
python scripts/plugin_provenance_doctor.py
python -m pytest tests/
git diff --check
python scripts/docs_doctor.py docs
python scripts/status_doctor.py
git diff --check
```

Result: passed (`525 passed`; later docs cleanup checks passed without rerunning
the full pytest suite).

## Bibliography and citation-plugin cleanup

Timestamp: 2026-06-29T12:02:08Z

Scope:

- changed the bundled `obsidian-citation-plugin` config to read generated
  `references.bib` instead of the retired `.memoria/memoria.bib`;
- redirected the plugin's unavoidable literature-note output to ignored
  `.memoria/staging/catalog` scratch so it cannot create live source Concepts;
- updated the plugin provenance digest for the changed config file;
- updated current setup, Zotero, export, troubleshooting, deployment, plugin,
  and on-disk-layout docs to describe worker-generated `references.bib` and no
  Better BibTeX auto-export into the vault.

Verification:

```bash
python scripts/plugin_provenance_doctor.py
python -m pytest tests/test_plugin_provenance.py -q
python scripts/docs_doctor.py docs
python scripts/status_doctor.py
python scripts/agents_doctor.py
python -m pytest tests/test_installer_skeleton.py tests/test_capture.py tests/test_projections.py tests/test_worker_queue.py tests/test_plugin_provenance.py -q
git diff --check
```

Result: passed (`5 passed`; focused projection/worker/plugin pytest run:
`83 passed`; `git diff --check` emitted only the existing `scripts/install.ps1`
LF/CRLF warning).
