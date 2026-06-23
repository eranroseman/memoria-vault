---
title: Obsidian workspaces
parent: Reference
---

# Obsidian workspaces

Memoria ships one saved Obsidian workspace named **Memoria** in
`src/.obsidian/workspaces.json`. It is a reset layout, not the space switcher
([ADR-81](../adr/81-persistent-gate-dashboards.md)).

Space switching happens through the navigation rail — the pinned `_nav.md` note in
the left pane. Its **Now** section surfaces the Inbox queue (count + health dot), and
its **Places** section links the three durable spaces:

| Space | Job | Dashboard |
| --- | --- | --- |
| Library | Collect and organize sources | `spaces/library.md` |
| Knowledge | Build and test claims | `spaces/knowledge.md` |
| Project | Steer bounded inquiry to output | `spaces/project.md` |

The Inbox queue (`spaces/inbox.md`, `type: queue`) is reached from the rail's **Now**,
not from **Places**. Each space dashboard embeds the relevant Bases views; the rail owns
switching, so the dashboards no longer carry a nav row. Clicking a rail link opens that
dashboard in the active tab; it does not load a new workspace layout.

On launch Obsidian natively restores your last session. On a fresh vault or layout reset,
the **Memoria** workspace seeds `home.md`, a thin first-run welcome note — there is no
forced landing surface.

## Reset layout

The **Memoria** workspace has one shared shell:

- **Main pane** — `home.md`, the first-run welcome note, opened in reading view.
- **Left sidebar** — the `_nav.md` navigation rail; primary movement happens through the
  rail and the Bases views on each space dashboard.
- **Right sidebar** — the Co-PI Agent Client chat view.

The core Workspaces plugin stays enabled so you can restore this shell with Obsidian's
own **Manage workspaces** command if panes get rearranged. Workspace switching is
not exposed through QuickAdd commands or loader scripts.

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
- The Co-PI pane: [Agent-client pane](../how-to-guides/using-obsidian/use-the-acp-pane.md)
