---
title: Use the reset workspace
parent: Using Obsidian
nav_order: 2
---

# Use the reset workspace

Memoria's daily navigation is the four gate dashboards, not saved workspace switching.
Use the saved **Memoria** workspace only when you want to reset a rearranged window.

## Prerequisites

- The vault open in Obsidian
- The Workspaces core plugin enabled (it ships enabled)

## Steps

**1. Switch gates from the dashboard nav row.**

Start from Inbox. Each gate dashboard links to the others:

- `gates/inbox.md` — triage what needs the PI now
- `gates/library.md` — collect and organize sources
- `gates/knowledge.md` — build and test claims
- `gates/project.md` — steer bounded inquiry to output

**2. Reset the shell only when needed.**

If panes are disarranged, use Obsidian's command palette:
`Cmd/Ctrl-P` → **Workspaces: Manage workspaces** → load **Memoria**.

The reset layout opens Inbox in the main pane, keeps file navigation on the left, and
keeps the Co-PI pane on the right.

## Verify

- The Homepage plugin opens `gates/inbox.md` on startup.
- Each gate dashboard links to the other three gates.
- Loading the **Memoria** workspace restores the shared shell without changing the
  gate model.

## Related

- Workspace reference: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- Opening the Co-PI pane: [Agent-client pane](use-the-acp-pane.md)
- Opening dashboards: [Navigate the dashboards](navigate-the-dashboards.md)
- The gate decision: [ADR-81](../../adr/81-persistent-gate-dashboards.md)
