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
| Are plugins bundled or implemented? | No plugin source, manifest, package, command, UI panel, or plugin test ships in alpha.15. |
| Does setup install Obsidian plugins? | No. |
| Does runtime depend on Local REST, Agent Client, Dataview, or QuickAdd? | No. |
| Where is the boundary checked? | `scripts/plugin_provenance_doctor.py` is a negative guard: it verifies removed plugin payload paths and common Obsidian adapter implementation paths stay absent. |

## Future adapters

Alpha.15 does not specify or ship an Obsidian adapter. If one is scheduled
later, it needs its own ADR and must be a thin caller of the stable CLI/engine.
It cannot own source authority, operation manifests, request lifecycle, write
policy, qmd indexing, checks, or recovery.

## Related

- CLI command reference: [Memoria CLI](cli.md)
- External integrations: [External integrations](integrations.md)
- Obsidian command-palette boundary: [Obsidian command palette](obsidian-command-palette.md)
