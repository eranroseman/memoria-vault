---
title: Obsidian workspaces
parent: Reference
---

# Obsidian workspaces

Two saved Obsidian workspace layouts ship in [src/.obsidian/workspaces.json](../../src/.obsidian/workspaces.json): **Home** and **Library**. A **Project** workspace arrives with the v0.1.0-alpha.3 Project release.

The Workspaces core plugin ships pre-enabled in the vault (`.obsidian/core-plugins.json`). Loading a layout is done from the command palette ("Workspaces: Load workspace"); see [Set up Obsidian](../how-to-guides/setup/set-up-obsidian.md) for the activation steps.

---

## The two workspaces

| Workspace | Left pane | Main pane | Right pane | Use |
| --- | --- | --- | --- | --- |
| **Home** (default) | File explorer | `home.md` (preview) — the homepage carries the daily glance | `system/dashboards/board-state.md` (the Inbox board) | The morning look: what needs me? |
| **Library** | Three tabs: `reading-pipeline`, `discuss-queue`, `catalog.base` | Empty — your reading/working tab | Backlinks | Library sessions: classify, read, discuss. |

---

## Coming in v0.1.0-alpha.3

The **Project** workspace (project tree + draft + verification context) ships with the Project release alongside the `projects/` workflow surfaces. Until then, project work happens in ad-hoc tabs.

---

## Layout storage

Layouts are saved in `.obsidian/workspaces.json`. If you customize them, verify the file is versioned in your vault repo (`git status .obsidian/`).

Each workspace maps to a cognitive mode (the "what needs me?" look, reading, drafting) rather than to a topic or project — the reasoning is in [Visual-style discipline](../explanation/obsidian/visual-discipline.md).

---

## Related

- The dashboards the panes open: [Dashboards](dashboards.md)
- The plugin set behind the panes: [Obsidian plugins](obsidian-plugins.md)
- The co-PI pane you pair these with: [Profile capabilities](profiles.md)
- Why workspaces map to cognitive modes: [Visual-style discipline](../explanation/obsidian/visual-discipline.md)
