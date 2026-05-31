---
topic: plugins
---

# zotlit — future migration target (not currently used)

ZotLit is faster than [obsidian-citation-plugin](../../docs/reference/plugins.md) for bulk imports (reads Zotero's SQLite database directly instead of parsing a BibTeX file) and supports image annotation import. It is **not currently recommended for production use** because of unresolved Zotero 7 compatibility issues (tracked in ZotLit's own release notes). Memoria holds it as a migration target rather than an alternative:

- **Adopt when:** the human's bulk-import volume justifies the switch (typically scoping reviews or systematic reviews requiring dozens of papers ingested at once) **and** Zotero 7 stability is confirmed in ZotLit's release notes.
- **Do not adopt to:** speed up the daily one-paper-at-a-time flow. The `obsidian-citation-plugin` path is fast enough for that, and the migration cost (re-aligning the paper-note template, re-validating the schema) is not worth it.

If migration ever happens, the load-bearing settings on the ZotLit side will be `databaseDir` (path to Zotero data), `citationLibrary` (must match the same Better BibTeX export the citation plugin used so citekey vocabulary stays stable), and a `noteTemplate` that re-creates the citation-plugin's `_proposed_classification` and `_enrichment` block discipline.
