---
title: Use the reset workspace
parent: Using Obsidian
nav_order: 2
---

# Use the reset workspace

Memoria's daily navigation is the left-pane rail, not saved workspace switching.
Use the saved **Memoria** workspace only when you want to reset a rearranged window.

## Prerequisites

- The vault open in Obsidian
- The Workspaces core plugin enabled (it ships enabled)

## Steps

**1. Switch surfaces from the left-pane rail.**

The pinned **Navigator** (`_nav.md`) owns switching. Its *Now* opens the Inbox queue; its *Places* open the three spaces:

- `spaces/inbox.md` — the queue: triage what needs the PI now
- `spaces/library.md` — collect and organize sources
- `spaces/knowledge.md` — build and test claims
- `spaces/project.md` — steer bounded inquiry to output

**2. Reset the shell only when needed.**

If panes are disarranged, use Obsidian's command palette:
`Cmd/Ctrl-P` → **Workspaces: Manage workspaces** → load **Memoria**.

The reset layout opens `home.md` in the main pane, keeps file navigation on the left, and
keeps the Agent Client pane on the right.

## Verify

- On launch, Obsidian restores your last session; a fresh vault or reset opens `home.md`.
- The left-pane rail switches among the three spaces and the Inbox queue.
- Loading the **Memoria** workspace restores the shared shell without changing the
  gate model.

## Related

- Workspace reference: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- Conversation surface: [Agent Client pane](use-the-agent-client-pane.md)
- Opening dashboards: [Navigate the dashboards](navigate-the-dashboards.md)
- The gate decision: [ADR-81](../../adr/81-persistent-gate-dashboards.md)
