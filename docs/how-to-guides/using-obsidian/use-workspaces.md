---
title: Workspaces
parent: Using Obsidian
nav_order: 2
---

# Workspaces

Switch between Memoria's three shipped pane layouts — **Desk**, **Library**, and **Studio** — without rebuilding your panes by hand.

## Prerequisites

- The vault open in Obsidian

The **Workspaces** core plugin ships pre-enabled in the vault (`.obsidian/core-plugins.json`), so the workspaces icon is already in the left ribbon — no first-run toggle needed.

## Steps

**1. Load a workspace by name.**

All three layouts ship pre-configured in the vault's `.obsidian/workspaces.json` (pane-by-pane contents: [Obsidian workspaces](../../reference/obsidian-workspaces.md)). The fastest path is one palette command per workspace — `Cmd/Ctrl-P` →

- `Memoria: open Desk workspace` — the "what needs me?" gate: next PI actions in the main pane, the Inbox queue on the left
- `Memoria: open Library workspace` — reading and synthesis: sources, Catalog records, and claims in the main pane, catalog and discussion queues on the left
- `Memoria: open Studio workspace` — drafting: research focus, claims, and patterns in the main pane, claims and patterns on the left

The same three commands back the workspace buttons on `home.md` ([Vault homepage](use-the-vault-homepage.md)). The core plugin's own UI works too: click the workspaces icon in the left ribbon (or `Cmd/Ctrl-P` → **Manage workspaces**) and load by name.

Switch when your cognitive mode changes — not per task within a mode. In every workspace the Co-PI chat pane is pinned on the right, so the conversation travels with you.

**2. (Optional) Bind hotkeys.**

No workspace hotkeys ship by default. For one-key switching: Settings → Hotkeys → search `Memoria: workspace` → assign e.g. `Ctrl-1` to **Desk**, `Ctrl-2` to **Library**, `Ctrl-3` to **Studio**.

**3. Save changes to a workspace** (when you've rearranged panes).

`Cmd/Ctrl-P` → **Manage workspaces** → click **Save** next to the workspace name. Unsaved layout changes revert when you next switch away — which is the feature: layout experiments don't stick unless you save them.

## Verify

- Loading **Desk**, then **Library**, then **Studio** swaps to three distinct pane layouts without reloading Obsidian
- The ACP pane (the Co-PI) is present on the right in all three, and keeps its session across switches

## Related

- Workspace layout reference (what each pane shows): [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- The control panel with the workspace buttons: [Vault homepage](use-the-vault-homepage.md)
- Opening the Co-PI pane: [Agent-client pane](use-the-acp-pane.md)
- Opening dashboards: [Navigate the dashboards](navigate-the-dashboards.md)
- Why few workspaces, not many: [Visual-style discipline](../../explanation/obsidian/visual-discipline.md)
