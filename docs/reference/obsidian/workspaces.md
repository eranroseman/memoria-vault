
# Workspaces

Three saved Obsidian workspace layouts, bound to hotkeys. One per cognitive mode.

**Prerequisite:** The Workspaces core plugin must be enabled (Settings → Core plugins → Workspaces). The bindings have nothing to bind to until the plugin is on.

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

These are **workspace layout** bindings (`Cmd/Ctrl` + number). They are distinct from **ACP profile-switch** bindings (`Ctrl+Shift` + number), which switch the active Hermes profile in the agent-client pane. The two sets share the same number keys but use different modifiers and do not collide.

| Binding | Action |
| --- | --- |
| `Cmd-1` / `Ctrl-1` | Switch to Human workspace |
| `Cmd-2` / `Ctrl-2` | Switch to Reading & Processing workspace |
| `Cmd-3` / `Ctrl-3` | Switch to Drafting workspace |
| `Ctrl+Shift+1` | Switch ACP pane to Socratic profile |
| `Ctrl+Shift+2` | Switch ACP pane to Mapper profile |
| `Ctrl+Shift+3` | Switch ACP pane to Writer profile |
| `Ctrl+Shift+4` | Switch ACP pane to Verifier profile |

---

## Design rules

- One workspace per cognitive mode, not per topic or project.
- Three is the working set. A fourth workspace means a hotkey the human will forget.
- Workspace configurations are saved in `.obsidian/workspaces.json` (gitignored in some vault configurations — verify with `git status .obsidian/`).

---

## Related

- Dashboard in Human workspace (left): [daily-health](../../explanation/dashboards/daily-health.md)
- Dashboard in Human workspace (right): [board-state](../../explanation/dashboards/board-state.md)
- Dashboard in Reading workspace (left, primary): [discuss-queue](../../explanation/dashboards/discuss-queue.md)
- Dashboard in Reading workspace (left, secondary): [reading-pipeline](../../explanation/dashboards/reading-pipeline.md)
- ACP pane profiles: [agent-client plugin](../plugins.md)
