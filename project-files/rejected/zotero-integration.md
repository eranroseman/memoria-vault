---
topic: plugins
---

# zotero-integration — evaluated alternative, not in use

[Zotero Integration](https://github.com/mgmeyers/obsidian-zotero-integration) (by mgmeyers) connects to Zotero's **local HTTP API while Zotero is running**, supporting color-coded annotation imports and Nunjucks note templates. It sits between the two ingest paths Memoria already documents: more capable than the BibTeX-file [obsidian-citation-plugin](../../docs/reference/zotero-plugins.md) (the current required path), lighter-touch than the SQLite-direct [zotlit](zotlit.md) (the future-migration target).

Memoria holds it on record but **does not use it**:

- **Switch to this if** the annotation workflow ever moves *out* of Obsidian and *into* Zotero — color-coded highlights pulled from Zotero into structured paper notes is the use case it wins on.
- **Don't switch while** Memoria's design assumes PDF annotation happens in Obsidian via [pdf-plus](../../docs/reference/obsidian-plugins.md). Flipping the annotation direction changes the human's daily rhythm — a bigger decision than a plugin swap.
