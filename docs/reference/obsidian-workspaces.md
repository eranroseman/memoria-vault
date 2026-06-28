---
title: Obsidian workspaces
parent: Obsidian and Zotero
grand_parent: Reference
---

# Obsidian workspaces

Memoria ships one saved Obsidian workspace named **Memoria** in
`src/.obsidian/workspaces.json`. It is a reset layout, not the space switcher
([ADR-81](../adr/81-persistent-gate-dashboards.md)). Space switching happens
through the pinned `_nav.md` rail note in the left pane.

## Rail targets

| Space | Job | Dashboard |
| --- | --- | --- |
| Library | Collect and organize sources | `spaces/library.md` |
| Knowledge | Build and test claims | `spaces/knowledge.md` |
| Project | Steer bounded inquiry to output | `spaces/project.md` |

The rail's **Now** section links the Inbox queue (`spaces/inbox.md`) and
Maintenance collection (`spaces/maintenance.md`). Its **Places** section links the
three durable spaces above.

## Startup behavior

On launch QuickAdd runs `Memoria: restore shell on startup`. If the pinned rail is
already present, it reveals the shell and leaves the main pane where Obsidian
restored it. If the rail is missing, it loads the saved **Memoria** workspace.

## Reset layout

The **Memoria** workspace has one shared shell:

- **Main pane** — `home.md`, the launch/reset welcome note, opened in reading view.
- **Left sidebar** — two tabs: the `_nav.md` navigation rail (surface switching) and a
  core file-explorer leaf. Portals replaces that visible explorer surface at runtime and
  hides `system/` and `.memoria/`. Primary movement happens through the rail and the
  Bases views on each space dashboard; Portals is for browsing the underlying notes.
- **Right sidebar** — the Co-PI Agent Client chat view.

The core Workspaces plugin stays enabled so startup can repair a missing rail and
so you can restore the reset shell manually with Obsidian's own **Manage
workspaces** command if panes get rearranged.

## Layout storage

The reset layout is saved in `.obsidian/workspaces.json`. Runtime state such as
`.obsidian/workspace.json` remains per-machine and is not part of the golden copy.

---

## Related

- Dashboard decision: [ADR-81](../adr/81-persistent-gate-dashboards.md)
- The superseded workspace model: [ADR-68](../adr/68-workspaces-desk-library-studio.md)
- The dashboard roster: [Dashboards](dashboards.md)
- The plugin set behind the panes: [Obsidian plugins](obsidian-plugins.md)
- Conversation surface: [Agent Client pane](../how-to-guides/using-obsidian/use-the-agent-client-pane.md)
