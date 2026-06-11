---
title: Obsidian workspaces
parent: Reference
---

# Obsidian workspaces

Two saved Obsidian workspace layouts ship in [src/.obsidian/workspaces.json](../../src/.obsidian/workspaces.json): **Home** and **Library**. A **Project** workspace arrives with the v0.1.0-alpha.3 Project release.

**Prerequisite:** the Workspaces core plugin ships pre-enabled in the vault (`.obsidian/core-plugins.json`). If you ever disable it, re-enable under Settings → Core plugins → Workspaces; switch layouts via the command palette ("Workspaces: Load workspace").

---

## The two workspaces

| Workspace | Left pane | Main pane | Right pane | Use |
| --- | --- | --- | --- | --- |
| **Home** (default) | File explorer | `home.md` (preview) — the homepage carries the daily glance | `system/dashboards/board-state.md` (the Inbox board) | The morning look: what needs me? |
| **Library** | Three tabs: `reading-pipeline`, `discuss-queue`, `catalog.base` | Empty — your reading/working tab | Backlinks | Library sessions: classify, read, discuss. |

The installer's next-steps point here: open the co-PI pane (`hermes -p memoria-copi acp` or the Agent Client pane), then switch to the Library workspace to work the reading pipeline.

---

## Coming in v0.1.0-alpha.3

The **Project** workspace (project tree + draft + verification context) ships with the Project release alongside the `projects/` workflow surfaces. Until then, project work happens in ad-hoc tabs.

---

## Design rules

- One workspace per cognitive mode, not per topic or project.
- Layouts are saved in `.obsidian/workspaces.json` — verify it is versioned in your vault repo if you customize (`git status .obsidian/`).

---

## Related

- The dashboards the panes open: [Dashboards](dashboards.md)
- The plugin set behind the panes: [Obsidian plugins](obsidian-plugins.md)
- The co-PI pane you pair these with: [Profile capabilities](profiles.md)
