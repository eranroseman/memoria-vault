---
title: Workspaces
parent: Using Obsidian
nav_order: 2
---

# Workspaces

Switch between Memoria's two shipped pane layouts — **Home** and **Library** — without rebuilding your panes by hand.

## Prerequisites

- The vault open in Obsidian

The **Workspaces** core plugin ships pre-enabled in the vault (`.obsidian/core-plugins.json`), so the workspaces icon is already in the left ribbon — no first-run toggle needed.

## Steps

**1. Load a workspace by name.**

Both layouts ship pre-configured in the vault's `.obsidian/workspaces.json` (pane-by-pane contents: [Obsidian workspaces](../../reference/obsidian-workspaces.md)):

- Click the workspaces icon in the left ribbon (or `Cmd/Ctrl-P` → **Manage workspaces**)
- Load **Home** — `home.md` front and center: the above-the-fold inbox and the daily glance
- Load **Library** — the reading-and-processing layout: catalog and notes side by side

Switch when your cognitive mode changes — not per task within a mode. A **Project** workspace arrives with the v0.1.2 Project release.

**2. (Optional) Bind hotkeys.**

No workspace hotkeys ship by default. For one-key switching: Settings → Hotkeys → search `Load workspace` → assign e.g. `Ctrl-1` to **Home** and `Ctrl-2` to **Library**.

**3. Save changes to a workspace** (when you've rearranged panes).

`Cmd/Ctrl-P` → **Manage workspaces** → click **Save** next to the workspace name. Unsaved layout changes revert when you next switch away — which is the feature: layout experiments don't stick unless you save them.

## Verify

- Loading **Home** then **Library** swaps to a distinct pane layout without reloading Obsidian
- The ACP pane (the co-PI) keeps its session across workspace switches

## Related

- Workspace layout reference (what each pane shows): [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- The homepage the Home layout centers on: [Vault homepage](use-the-vault-homepage.md)
- Opening the co-PI pane: [Agent-client pane](use-the-acp-pane.md)
- Opening dashboards: [Navigate the dashboards](navigate-the-dashboards.md)
- Why few workspaces, not many: [Visual-style discipline](../../explanation/obsidian/visual-discipline.md)
