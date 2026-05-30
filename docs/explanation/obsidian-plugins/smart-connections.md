---
topic: plugins
---

# smart-connections + markdb-connect

Recommended. Neither `smart-connections` nor `markdb-connect` has load-bearing settings; default configurations are fine. If using `smart-connections` for vector search, ensure the embeddings model matches Memoria's [model routing config](../../reference/architecture/capability-stack.md#model-routing-synthesis-on-claude-cheap-tasks-elsewhere) — embedding calls should go to the cheap model tier, not Claude.

`smart-connections` is best treated as a **parallel peer to Memoria, not a wired component**. Use it for synchronous in-Obsidian semantic search (mid-draft "what notes do I have on X?"); do **not** try to feed its embeddings into Memoria's Mapper. Memoria's retrieval substrate (`qmd` and the search skills in [workflows/README.md](../../how-to/workflows/README.md)) is purpose-built for agent use; Smart Connections is purpose-built for human use. Use both, separately. Your attention is the integration layer.

If a cross-system bridge ever becomes necessary, the only practical option is the community-maintained `msdanyg/smart-connections-mcp` server, which exposes Smart Connections' embeddings over MCP by reading its `.smart-env/*.ajson` files. Caveats: single contributor, small footprint, and dependent on an undocumented storage format that changes between releases — it ships as a community optimization, not as load-bearing infrastructure. Adopt only if Smart Connections is already a daily driver *and* a concrete agent use case appears that can't be served by Memoria's own retrieval; otherwise the cost (forking and maintaining a bridge against an undocumented format) outweighs the saved embedding compute.

`markdb-connect` (full name [zotero-markdb-connect](https://github.com/daeh/zotero-markdb-connect)) is a **Zotero add-on, not an Obsidian plugin** — it is installed *in Zotero* (like Better BibTeX), not under `.obsidian/plugins/`. It scans a configured folder of vault Markdown for citekeys and tags the matching Zotero items, so you can see at a glance which papers already have notes. Useful for the [ingest workflow](../../how-to/workflows/upstream/ingest.md). (The "smart-connections + markdb-connect" pairing in this file's title is editorial — the two tools sit on opposite sides of the Zotero/Obsidian boundary.)
