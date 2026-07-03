---
title: Obsidian plugins
parent: Obsidian and Zotero
grand_parent: Reference
---

# Obsidian plugins

Alpha.15 does not ship or require Obsidian plugins. Memoria is a standalone CLI
and engine; the workspace template contains Markdown keep-set files, SQLite
state, qmd search state, and auxiliary Memoria files only.

## Baseline

| Question | Alpha.15 answer |
| --- | --- |
| Are plugins bundled? | No. |
| Does setup install Obsidian plugins? | No. |
| Does runtime depend on Local REST, Agent Client, Dataview, or QuickAdd? | No. |
| Where is plugin provenance checked? | Nowhere in the baseline; `scripts/plugin_provenance_doctor.py` verifies the deleted payload stays absent. |

## Optional adapters

A future Obsidian adapter is specified as a thin client, but its implementation
is excluded from alpha.15. It must be a caller of the stable CLI/engine and
cannot own source authority, operation manifests, request lifecycle, write
policy, qmd indexing, checks, or recovery.

## Related

- CLI command reference: [Memoria CLI](cli.md)
- External integrations: [External integrations](integrations.md)
- Obsidian command-palette boundary: [Obsidian command palette](obsidian-command-palette.md)
