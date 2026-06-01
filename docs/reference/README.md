
# Reference

Lookup material for Memoria — fields, values, commands, schemas, folder paths. For design rationale and conceptual explanations, see [explanation/](../explanation/).

The files are grouped below by domain for scanning; the folder itself is flat.

## Vault data model

| File | What it covers |
| --- | --- |
| [frontmatter.md](frontmatter.md) | Every YAML frontmatter field: type, allowed values, owner, namespace |
| [note-types.md](note-types.md) | The 16 note types: folder, template, lifecycle, promotion map |
| [linking.md](linking.md) | Wikilink conventions, typed-relation vocabulary, MOC thresholds |
| [kanban-board.md](kanban-board.md) | Kanban state machine, card schema, review overlay, WIP limits |
| [glossary.md](glossary.md) | Term definitions, alphabetical |

## Agents and control

| File | What it covers |
| --- | --- |
| [profiles.md](profiles.md) | Lane identifiers, capability table, invocation levels, folder permissions |
| [linter.md](linter.md) | Linter structural detectors, auto-fix classes, and severity scale |
| [command-palette.md](command-palette.md) | Obsidian `Memoria:` command-palette entries (the in-Obsidian UI surface) |
| [hermes-cli.md](hermes-cli.md) | All `hermes …` CLI commands: per-profile research, board management, profile/skills/cron admin |
| [policy-mcp.md](policy-mcp.md) | Policy MCP: decision values, request/response contract, audit log format, auto-fix classes |
| [computational-toolbox.md](computational-toolbox.md) | Deterministic and hybrid methods: embeddings, classifiers, clustering, NLI, graph algorithms |

## Pipelines and I/O

| File | What it covers |
| --- | --- |
| [ingest.md](ingest.md) | Type detection dispatch, per-type enrichment, frontmatter written at ingest |
| [export.md](export.md) | Citation states, export routes, editor comparison, deliverable targets |
| [memory.md](memory.md) | Memory substrate table, audit log schema, log rotation spec |

## System and infrastructure

| File | What it covers |
| --- | --- |
| [integrations.md](integrations.md) | External APIs and tools: enrichment, entity resolution, vault access, execution layer |
| [on-disk-layout.md](on-disk-layout.md) | Vault folder tree, `.memoria/` layout, skeleton notes, naming conventions |
| [failure-modes.md](failure-modes.md) | All failure modes by severity: symptom, cause, fix |
| [bibliography.md](bibliography.md) | Works cited across the docs, in ACM author-date style; in-text citations link here |

## Obsidian

| File | What it covers |
| --- | --- |
| [obsidian-plugins.md](obsidian-plugins.md) | Obsidian plugin inventory and load-bearing configuration settings |
| [zotero-plugins.md](zotero-plugins.md) | Zotero add-ons and the Zotero↔Obsidian connector comparison |
| [obsidian-callouts.md](obsidian-callouts.md) | Callout type identifiers, trigger conditions, and field schema |
| [obsidian-status-line.md](obsidian-status-line.md) | Status-line format, field definitions, and update cadence |
| [obsidian-workspaces.md](obsidian-workspaces.md) | Workspace names, layout rules, and switching conventions |
