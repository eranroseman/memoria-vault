---
title: Vault launch screen
parent: Using Obsidian
grand_parent: How-to guides
nav_order: 1
---

# Vault launch screen

On startup — and after a layout reset — you land on the vault-root `home.md` welcome note: a short "start here" screen that points you at loading the tutorial sample, capturing your first source, the three places (Library · Knowledge · Project), and asking the Co-PI. Navigation between surfaces is the left-pane rail ([ADR-116](../../adr/116-obsidian-surface-architecture.md)).

## Prerequisites

- The vault open in Obsidian

## Steps

**1. Land on the welcome note.**

On startup or a layout reset, the saved **Memoria** workspace seeds `home.md` — a welcome note. It is a "start here" screen, not a dashboard: load the tutorial sample, capture your first source, meet the three places, and ask the Co-PI. To return to this clean layout at any time, use the saved Memoria workspace ([Use the reset workspace](reset-workspace.md)).

**2. Switch spaces from the rail.**

The left-pane rail (`_nav.md`) owns navigation. Under **Now** it shows the Inbox
action count plus the Maintenance drift band; under **Places** it links
**Library** · **Knowledge** · **Project**. Click a place to open that space in
the active tab; reach the queue and Maintenance from **Now**.

**3. Act from the action row.**

Use the ribbon or command palette for capture/delegation actions: **Capture fleeting**, **Capture from Zotero**, **Capture URL**, **Delegate a task**, **Resolve card**, and **Agent Client: Open chat view**. Each dispatches the matching palette command — the visible controls are shortcuts, not a second mechanism.

**4. Drill down from the index.**

The three spaces group the day-to-day views by job: Library, Knowledge, and Project, with the Inbox queue as the triage surface. For the full dashboard roster see [Surfaces, Bases, and dashboards](../../reference/dashboards.md); to pick the right one for a situation, see [Navigate Memoria surfaces](navigate-memoria-surfaces.md).

Keep `steering.md` current — the Librarian reads it at the start of every session to set discovery targets. Update it at least weekly during the Friday ritual.

## Verify

- Startup or layout reset lands on the `home.md` welcome note with the rail pinned
- The left-pane rail shows the Inbox action count and Maintenance drift band under **Now**, and **Library** · **Knowledge** · **Project** under **Places**
- Clicking **Capture fleeting** opens the QuickAdd capture prompt

## Related

- Why the launch screen is a plain note, not a custom app: [Home welcome note](../../explanation/obsidian/home.md)
- The surface architecture decision: [ADR-116](../../adr/116-obsidian-surface-architecture.md)
- What each dashboard shows: [explanation/dashboards/](../../explanation/dashboards)
- The reset workspace: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- Updating steering on schedule: [Run the weekly review](../inbox/run-the-weekly-review.md)
