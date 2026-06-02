---
title: How to use workspaces
parent: Using Obsidian
---

# How to use workspaces

Switch between Memoria's three cognitive-mode workspaces — Human, Reading & Processing, and Drafting — using a single hotkey.

## Prerequisites

- The vault open in Obsidian
- **Workspaces** core plugin enabled (Settings → Core plugins → Workspaces)

## Steps

**1. Enable the Workspaces plugin** (first time only).

Settings → Core plugins → scroll to **Workspaces** → toggle on. Once enabled, a workspaces icon appears in the left ribbon.

**2. Open each workspace by name.**

The three workspaces ship pre-configured in the vault's `.obsidian/workspaces.json`. Load them:

- Click the workspaces icon in the left ribbon (or `Cmd/Ctrl-P` → **Manage workspaces**)
- Load **Human** — verifies the Daily Health dashboard opens in the left pane
- Load **Reading & Processing** — verifies the discuss-queue + ACP pane open on the right
- Load **Drafting** — verifies the project tree opens on the left

**3. Bind the hotkeys** (first time only).

Settings → Hotkeys → search `workspace` → assign:

| Workspace | Hotkey |
| --- | --- |
| Load workspace: Human | `Cmd-1` / `Ctrl-1` |
| Load workspace: Reading & Processing | `Cmd-2` / `Ctrl-2` |
| Load workspace: Drafting | `Cmd-3` / `Ctrl-3` |

**4. Switch workspaces during a session.**

- `Cmd/Ctrl-1` — Human (morning glance, board review)
- `Cmd/Ctrl-2` — Reading & Processing (one source, full context)
- `Cmd/Ctrl-3` — Drafting (single-focus on the active draft)

Switch when your cognitive mode changes — not per task within a mode.

**5. Save changes to a workspace** (when you've rearranged panes).

`Cmd/Ctrl-P` → **Manage workspaces** → click **Save** next to the workspace name. Unsaved layout changes revert when you next switch away.

## Verify

- `Ctrl/Cmd-1`, `Ctrl/Cmd-2`, `Ctrl/Cmd-3` each load a distinct pane layout without reloading Obsidian
- The ACP profile-switch bindings (`Ctrl+Shift+1–4`) still work independently from within the Reading workspace

## Related

- Workspace layout reference (what each pane shows): [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- Opening the ACP pane within Reading workspace: [How to use the agent-client pane](use-the-acp-pane.md)
- Opening dashboards: [How to navigate the dashboards](navigate-the-dashboards.md)
- Why three workspaces, not more: [Visual-style discipline](../../explanation/obsidian/visual-discipline.md)
