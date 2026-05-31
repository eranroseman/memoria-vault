---
topic: general
---

# Reference

Lookup material: exact fields, values, commands, and schemas, with no narrative. Reach for these when you know *what* you're doing and need the precise detail. For the reasoning behind any of it, see [explanation/](../explanation/).

## Schemas & vocabulary

- [glossary.md](glossary.md) — cross-cutting terms, grouped by domain, with a disambiguations section.
- [frontmatter-schema.md](frontmatter-schema.md) — YAML frontmatter fields and controlled vocabularies.
- [vocabulary-example.md](vocabulary-example.md) — a worked HCI/digital-health vocabulary for the open `topic` / `study_design` / `methods` fields (an example to copy-and-edit, not a default).
- [note-types.md](note-types.md) — the fifteen note types and their lifecycles.
- [linking-patterns.md](linking-patterns.md) — wikilink, typed-relation, and MOC conventions.
- [on-disk-layout.md](on-disk-layout.md) — the vault folder tree and what each folder holds.

## Board

- [board-states.md](board-states.md) — the Kanban state machine, lanes, and review gate.
- [card-schema.md](card-schema.md) — Hermes card fields, metadata overlay, and handoff payload.
- [lane-naming.md](lane-naming.md) — the single lane identifier (the `memoria-<name>` assignee) and the profile ↔ override-file ↔ assignee table.

## Commands

- [command-catalog.md](command-catalog.md) — the full catalog of `Memoria:` commands and their implementation.
- [profile-commands.md](profile-commands.md) — the operational command catalog per profile.
- [profile-matrices.md](profile-matrices.md) — profile capability and permission matrices.

## Architecture

- [architecture/capability-stack.md](architecture/capability-stack.md) — the layered capability stack.
- [architecture/computational-toolbox.md](architecture/computational-toolbox.md) — the non-LLM computational methods available to profiles.
- [architecture/policy-mcp.md](architecture/policy-mcp.md) — the policy MCP permission and audit surface.

## Obsidian UI

- [obsidian-ui/dashboards.md](obsidian-ui/dashboards.md) — dashboard inventory and Dataview queries.
- [obsidian-ui/plugin-ui.md](obsidian-ui/plugin-ui.md) — plugin-provided UI surfaces.
- [obsidian-ui/status-line.md](obsidian-ui/status-line.md) — the status-line fields.
- [obsidian-ui/workspaces.md](obsidian-ui/workspaces.md) — the workspace layouts.

## Plugins (configuration reference)

- [plugins/](plugins/) — per-plugin configuration reference for every Obsidian plugin in the install set (and the held-knowledge ones), grouped by lifecycle: required, recommended, and reference-only.

## Templates

- [templates/design-summary-template.md](templates/design-summary-template.md) — the shared page skeleton for design summaries.
- [templates/design-system.md](templates/design-system.md) — the visual-style template.
