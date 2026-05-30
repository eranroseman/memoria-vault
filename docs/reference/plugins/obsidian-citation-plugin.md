---
topic: plugins
---

# obsidian-citation-plugin

The current Required plugin for getting Zotero references into the vault. Reads the BibTeX/BibLaTeX export Better BibTeX produces, exposes `@`-autocomplete for inserting citations, and creates paper notes from a configured template.

**Authoritative config:** shipped at `.obsidian/plugins/obsidian-citation-plugin/data.json` in the starter vault — a ready-to-use `data.json` ([suffix conventions](../../explanation/obsidian-plugins/plugin-configs-lifecycle.md#the-three-suffix-conventions)). It embeds the authoritative paper-note frontmatter (matching the schema in [vault/README.md](../../explanation/vault/README.md)) plus the `_proposed_classification` and `_enrichment` blocks detailed below.

Load-bearing settings:

- `citationExportPath` — absolute path to the Better BibTeX export. Memoria uses `.memoria/library.bib` (machine-read tool input, alongside the lane-overrides and CSL files). The legacy convention of naming the bib after the vault (`<vault-name>.bib`) is no longer used — `library.bib` aligns with the universal BibTeX convention and the Pandoc workflow's `--bibliography .memoria/library.bib` reference.
- `citationExportFormat: "biblatex"` — the modern BibLaTeX format; preserves Unicode and modern entry types better than legacy `bibtex`.
- `literatureNoteFolder` — must point at the paper-note literature folder (`20-sources/01-papers/` in Memoria's schema). Wrong folder means the plugin creates notes outside the Librarian's scope, and the Memoria Linter immediately flags them.
- `literatureNoteTitleTemplate: "@{{citekey}}"` — keeps the filename and citekey identical so backlinks resolve cleanly.
- `literatureNoteContentTemplate` — the body skeleton. **This is the setting that matters most.** It must include:
  - The full canonical frontmatter (see [vault/README.md](../../explanation/vault/README.md) for the schema and key order).
  - The `_proposed_classification` HTML comment block — Librarian fills it on ingest; human promotes to main frontmatter on classification.
  - The `_enrichment` HTML comment block — Librarian populates from API enrichment (citation count, scite, MeSH, OpenAlex concepts, etc.) and never touches main frontmatter for derived metrics.

The template is the source of truth for what a freshly-ingested paper note looks like. Drift between the template and the Librarian's expected schema breaks the classify and enrichment workflows. Treat changes to it as schema migrations — diff the change against [vault/README.md](../../explanation/vault/README.md) and the Librarian's contract in [librarian.md](../../explanation/profiles/librarian.md) before saving.

## Alternative: zotero-integration (Zotero Integration by mgmeyers)

For the evaluated alternative, see [zotero-integration](../../project/evaluated-alternatives/zotero-integration.md).
