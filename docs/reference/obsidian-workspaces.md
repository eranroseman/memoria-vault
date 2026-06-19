---
title: Obsidian workspaces
parent: Reference
---

# Obsidian workspaces

Memoria ships one saved Obsidian workspace named **Memoria** in
`src/.obsidian/workspaces.json`. It is a reset layout, not the space switcher
([ADR-81](../adr/81-persistent-gate-dashboards.md)).

Space switching happens through dashboard notes under `spaces/`:

| Gate | Job | Dashboard |
| --- | --- | --- |
| Inbox | Triage what needs the PI now | `spaces/inbox.md` |
| Library | Collect and organize sources | `spaces/library.md` |
| Knowledge | Build and test claims | `spaces/knowledge.md` |
| Project | Steer bounded inquiry to output | `spaces/project.md` |

The Homepage plugin opens `spaces/inbox` on startup. Each space dashboard embeds the
relevant Bases views and carries a nav row linking to the other spaces. Clicking a space
link opens that dashboard in the active tab; it does not load a new workspace layout.

## Reset layout

The **Memoria** workspace has one shared shell:

- **Main pane** — `spaces/inbox.md`, opened in reading view.
- **Left sidebar** — Portals folder navigation, with the core file explorer retained
  as fallback.
- **Right sidebar** — the Co-PI Agent Client chat view.

The core Workspaces plugin stays enabled so you can restore this shell with Obsidian's
own **Manage workspaces** command if panes get rearranged. The retired QuickAdd
workspace commands and loader script are not shipped.

Workspaces Plus was evaluated and rejected for the shipped path. It can register
native workspace-switching commands, but Memoria no longer models spaces as saved
workspace layouts; the dashboard-note navigation in `spaces/` is the source of
truth.

## Layout storage

The reset layout is saved in `.obsidian/workspaces.json`. Runtime state such as
`.obsidian/workspace.json` remains per-machine and is not part of the golden copy.

---

## Related

- Gate decision: [ADR-81](../adr/81-persistent-gate-dashboards.md)
- The superseded workspace model: [ADR-68](../adr/68-workspaces-desk-library-studio.md)
- The dashboard roster: [Dashboards](dashboards.md)
- The plugin set behind the panes: [Obsidian plugins](obsidian-plugins.md)
- The Co-PI pane: [Agent-client pane](../how-to-guides/using-obsidian/use-the-acp-pane.md)
