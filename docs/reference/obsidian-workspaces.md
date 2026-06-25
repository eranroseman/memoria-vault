---
title: Obsidian workspaces
parent: Reference
---

# Obsidian workspaces

Memoria ships one saved Obsidian workspace named **Memoria** in
`src/.obsidian/workspaces.json`. It is a reset layout, not the space switcher
([ADR-81](../adr/81-persistent-gate-dashboards.md)).

Space switching happens through the navigation rail — the pinned `_nav.md` note in
the left pane. Its **Now** section surfaces the Inbox queue action count and the
Maintenance/Fleet health band, and its **Places** section links the three durable spaces:

| Space | Job | Dashboard |
| --- | --- | --- |
| Library | Collect and organize sources | `spaces/library.md` |
| Knowledge | Build and test claims | `spaces/knowledge.md` |
| Project | Steer bounded inquiry to output | `spaces/project.md` |

The Inbox queue (`spaces/inbox.md`, `type: queue`) and Maintenance collection
(`spaces/maintenance.md`, `type: maintenance`) are reached from the rail's **Now**,
not from **Places**. Each space dashboard embeds the relevant Bases views; the rail
owns switching, so the dashboards no longer carry a nav row. Clicking a rail link opens
that dashboard in the active tab; it does not load a new workspace layout.

On launch QuickAdd runs the `Memoria: restore shell on startup` macro. It first lets
Obsidian restore your previous session; if the pinned `_nav.md` rail is already present,
the macro only reveals it and leaves the main pane where you were. If the rail is
missing, it falls back to Obsidian's core Workspaces plugin and loads the saved
**Memoria** workspace: `home.md` in the main pane, the pinned rail on the left, and the
Co-PI pane on the right. There is no Homepage plugin and no Inbox forced landing.

## Reset layout

The **Memoria** workspace has one shared shell:

- **Main pane** — `home.md`, the launch/reset welcome note, opened in reading view.
- **Left sidebar** — two tabs: the `_nav.md` navigation rail (surface switching) and the
  Portals curated file browser, which replaces the core file explorer and hides `system/`
  and `.memoria/`. Primary movement happens through the rail and the Bases views on each
  space dashboard; Portals is for browsing the underlying notes.
- **Right sidebar** — the Co-PI Agent Client chat view.

The core Workspaces plugin stays enabled so startup can repair a missing rail and so
you can restore the reset shell manually with Obsidian's own **Manage workspaces**
command if panes get rearranged. Space switching is not exposed through QuickAdd
commands or loader scripts.

Workspaces Plus was evaluated and rejected for the shipped path. It can register
native workspace-switching commands, but Memoria models spaces as dashboard notes
reached from the navigation rail, not saved workspace layouts; the rail and the
dashboard notes in `spaces/` are the source of truth.

## Layout storage

The reset layout is saved in `.obsidian/workspaces.json`. Runtime state such as
`.obsidian/workspace.json` remains per-machine and is not part of the golden copy.

---

## Related

- Gate decision: [ADR-81](../adr/81-persistent-gate-dashboards.md)
- The superseded workspace model: [ADR-68](../adr/68-workspaces-desk-library-studio.md)
- The dashboard roster: [Dashboards](dashboards.md)
- The plugin set behind the panes: [Obsidian plugins](obsidian-plugins.md)
- Conversation surface: [Agent Client pane](../how-to-guides/using-obsidian/use-the-agent-client-pane.md)
