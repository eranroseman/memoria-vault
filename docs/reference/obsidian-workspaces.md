---
title: Obsidian workspaces
parent: Obsidian and Zotero
grand_parent: Reference
---

# Obsidian workspaces

Alpha.14 ships no saved Obsidian workspace layout. The durable workspace shape is
the on-disk Memoria workspace plus CLI commands.

## Workspace navigation

| Area | Markdown entry point | CLI entry point |
| --- | --- | --- |
| Inbox | `spaces/inbox.md` | `memoria request list --workspace .` |
| Library | `spaces/library.md` | `memoria work capture`, `memoria work import`, `memoria work digest` |
| Knowledge | `spaces/knowledge.md` | `memoria ask`, `memoria workspace scan` |
| Project | `spaces/project.md` | `memoria project gaps`, `memoria project export` |
| Maintenance | `spaces/maintenance.md` | `memoria workspace check`, `memoria doctor` |

## Adapter rule

An optional editor workspace may be provided later, but it is presentation only.
It must not become the source of truth for navigation, request state, queued work,
checks, recovery, or generated projections.

## Related

- On-disk layout: [On-disk layout](on-disk-layout.md)
- CLI command reference: [Memoria CLI](cli.md)
- External integrations: [External integrations](integrations.md)
