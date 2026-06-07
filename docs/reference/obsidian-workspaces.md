---
title: Obsidian workspaces
parent: Reference
---


# Obsidian workspaces

Three saved Obsidian workspace layouts, bound to hotkeys. One per cognitive mode.

**Prerequisite:** The Workspaces core plugin ships pre-enabled in the vault (`.obsidian/core-plugins.json`); the three layouts ship in `.obsidian/workspaces.json`. If you ever disable the plugin, the bindings have nothing to bind to until you re-enable it (Settings → Core plugins → Workspaces).

---

## The three workspaces

| Workspace | Hotkey | Left pane | Main pane | Right pane | Use |
| --- | --- | --- | --- | --- | --- |
| **Human** | `Cmd-1` (`Ctrl-1` on Windows) | Daily Health | Empty / scratch | `board-state` | Default. Morning glance. 30 seconds. |
| **Reading & Processing** | `Cmd-2` (`Ctrl-2`) | `discuss-queue` (primary) + `reading-pipeline` | Source PDF (left split) + paper note (right split) | Backlinks + Outgoing links + Socratic ACP pane | Reading sessions. One source, full context. |
| **Drafting** | `Cmd-3` (`Ctrl-3`) | Project folder tree (`40-workbench/<project>/`) | Draft (full width) | Backlinks (linked claim notes) + verification report (bottom) | Project work. Single-focus on the active draft. |

---

## Hotkey bindings

Workspace hotkeys are configured under Settings → Hotkeys → search "workspace". The Workspaces core plugin must be enabled first.

These are **workspace layout** bindings (`Cmd/Ctrl` + number) — they switch the saved layout. Switching the Hermes profile inside the agent-client pane is a separate action with **no keyboard shortcut**: use the profile picker at the top of the pane (see [Agent-client pane](../how-to-guides/using-obsidian/use-the-acp-pane.md#switching-profiles)).

| Binding | Action |
| --- | --- |
| `Cmd-1` / `Ctrl-1` | Switch to Human workspace |
| `Cmd-2` / `Ctrl-2` | Switch to Reading & Processing workspace |
| `Cmd-3` / `Ctrl-3` | Switch to Drafting workspace |

---

## Design rules

- One workspace per cognitive mode, not per topic or project.
- Three is the working set. A fourth workspace means a hotkey the human will forget.
- Workspace configurations are saved in `.obsidian/workspaces.json` (gitignored in some vault configurations — verify with `git status .obsidian/`).

---

## Related

- ACP pane profiles: [agent-client plugin](obsidian-plugins.md)
- Dashboard in Human workspace (left): [The Daily Health dashboard](../explanation/dashboards/daily-glance/daily-health.md)
- Dashboard in Human workspace (right): [The board-state dashboard](../explanation/dashboards/daily-glance/board-state.md)
- Dashboard in Reading workspace (left, primary): [The discuss-queue dashboard](../explanation/dashboards/synthesis-agenda/discuss-queue.md)
- Dashboard in Reading workspace (left, secondary): [The reading-pipeline dashboard](../explanation/dashboards/synthesis-agenda/reading-pipeline.md)
