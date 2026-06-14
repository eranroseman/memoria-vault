---
title: Obsidian workspaces
parent: Reference
---

# Obsidian workspaces

Three saved Obsidian workspace layouts ship in `src/.obsidian/workspaces.json`: **Desk**, **Library**, and **Studio** ([ADR-68](../adr/68-workspaces-desk-library-studio.md)). Each maps to a cognitive mode — the "what needs me?" look, reading & synthesis, drafting — not to a topic or project; the reasoning is in [Visual-style discipline](../explanation/obsidian/visual-discipline.md).

The Workspaces core plugin ships pre-enabled in the vault (`.obsidian/core-plugins.json`). Load a layout with one of the `Memoria: workspace …` palette commands, the workspace buttons on `home.md`, or the core "Workspaces: Manage workspaces" modal; see [Workspaces](../how-to-guides/using-obsidian/use-workspaces.md).

---

## The shared layout contract

Every workspace follows the same shape:

- **Main pane** — the mode's work surface: a real file, never `home.md`, never an empty leaf.
- **Left sidebar** (~320) — navigation: 2–4 pinned tabs of that mode's drill-down views, with the **file explorer always the last tab**.
- **Right sidebar** (~360) — the Co-PI: the agent-client chat view, pinned in every workspace.
- `home.md` is pinned in **no** workspace — the obsidian-homepage plugin opens it on launch ([ADR-13](../adr/13-homepage-front-door.md)).

## The three workspaces

| Workspace | Mode | Main pane | Left tabs (in order) | Right pane |
| --- | --- | --- | --- | --- |
| **Desk** (default) | "What needs me?" | `system/dashboards/board-state.md` | `inbox/inbox.base` · `drift-watch.md` · `weekly-review.md` · file explorer | Co-PI chat |
| **Library** | Reading & synthesis | `system/dashboards/reading-pipeline.md` | `catalog/catalog.base` · `discuss-queue.md` · `open-questions.md` · `contradictions.md` · file explorer | Co-PI chat |
| **Studio** | Drafting | `research-focus.md` (`projects/` ships empty — the priorities note is the drafting anchor) | `system/dashboards/claims.base` · `system/patterns/patterns.base` · file explorer | Co-PI chat + backlinks |

Studio's right sidebar carries a second tab — the core backlink view — behind the Co-PI tab, so backlinks live where there is an active note. Studio replaces the "Project" workspace once planned for v0.1.0-alpha.3 ([ADR-68](../adr/68-workspaces-desk-library-studio.md)).

## Palette commands

Three QuickAdd choices give one-click switching (also wired to the workspace buttons on `home.md`):

| Palette entry | Loads |
| --- | --- |
| `QuickAdd: Memoria: open Desk workspace` | Desk |
| `QuickAdd: Memoria: open Library workspace` | Library |
| `QuickAdd: Memoria: open Studio workspace` | Studio |

All three run `system/scripts/load-workspace.js`, which loads the named layout through the core Workspaces plugin (the plugin has no per-workspace commands of its own).

## Layout storage

Layouts are saved in `.obsidian/workspaces.json`. `.base` files are pinned as `bases` leaves (the core Bases view); dashboards as `markdown` leaves in preview mode. If you customize a layout, verify the file is versioned in your vault repo (`git status .obsidian/`).

---

## Related

- The dashboards the panes open: [Dashboards](dashboards.md)
- The plugin set behind the panes: [Obsidian plugins](obsidian-plugins.md)
- The Co-PI pane every right sidebar pins: [Agent-client pane](../how-to-guides/using-obsidian/use-the-acp-pane.md)
- Why workspaces map to cognitive modes: [Visual-style discipline](../explanation/obsidian/visual-discipline.md)
- The decision record: [ADR-68](../adr/68-workspaces-desk-library-studio.md)
