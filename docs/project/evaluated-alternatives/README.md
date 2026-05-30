---
topic: general
---

# Evaluated alternatives

Tools that were evaluated and **not adopted** — either rejected for a structural reason, or held as a future-migration target if conditions change. They are kept on record so the reasoning behind each decision survives, and so a future revisit starts from where the last one left off. None of these is part of the install set; see [reference/plugins/](../../reference/plugins/) for what is.

- **[obsidian-kanban.md](obsidian-kanban.md)** — renders a single markdown file as a drag-and-drop board; **not adopted** because the authoritative board is the Hermes Kanban (`kanban.db`), rendered via Dataview, with no markdown file for the plugin to read.
- **[obsidian-linter.md](obsidian-linter.md)** — a GUI on-save Markdown formatter; **not in the install set** ([ADR-24](../decisions/24-obsidian-linter-reference-only.md)) because it would be a second frontmatter authority writing outside the policy-MCP audit trail. Safe-config knowledge is held in case a human runs it anyway.
- **[zotero-integration.md](zotero-integration.md)** — connects to Zotero's local HTTP API for annotation imports; **held, not used** — adopt only if the annotation workflow ever moves out of Obsidian and into Zotero.
- **[zotlit.md](zotlit.md)** — reads Zotero's SQLite database directly for fast bulk imports; a **future-migration target**, blocked on Zotero 7 stability and justified only when bulk-import volume warrants it.
