---
title: Vault homepage
parent: Using Obsidian
nav_order: 1
---

# Vault homepage

The obsidian-homepage plugin opens `spaces/inbox.md` on launch ([ADR-81](../../adr/81-persistent-gate-dashboards.md)). The vault-root `home.md` is a stable fallback note with a link to Inbox if the plugin is disabled or reset.

## Prerequisites

- The vault open in Obsidian

## Steps

**1. Open the launch surface.**

The obsidian-homepage plugin opens `spaces/inbox.md` automatically on launch in Reading view, replacing any open notes. It opens on demand too:

- `Cmd/Ctrl-P` → **Homepage: Open homepage**, or click the home ribbon icon
- Or open `spaces/inbox.md` from the space nav row, Portals, or the file explorer

To get back to a clean launch view at any time, **right-click a tab header -> Close all** — it closes every open tab and re-launches Inbox.

**2. Read the Inbox glance.**

The Inbox space's brief and top views are the morning check: Needs me, Drift watch, Loose ends, and Board. Empty means nothing urgent; under ten seconds to read.

**3. Act from the action row.**

Use the ribbon or command palette for capture/delegation actions: **Capture fleeting**, **Capture from Zotero**, **Capture URL**, **Delegate a task**, **Resolve card**, and **Agent Client: Open chat view**. Each dispatches the matching palette command — the visible controls are shortcuts, not a second mechanism.

**4. Navigate from the navigation row.**

The space nav row links **Inbox** · **Library** · **Knowledge** · **Project**. Click a space name to open that dashboard in the active tab. The saved **Memoria** workspace is only a reset layout ([Use the reset workspace](use-workspaces.md)).

**5. Drill down from the index.**

The four spaces group the day-to-day views by job: Inbox, Library, Knowledge, and Project. For the full dashboard roster see [Dashboards](../../reference/dashboards.md); to pick the right one for a situation, see [Navigate the dashboards](navigate-the-dashboards.md).

Keep `research-focus.md` current — the Librarian reads it at the start of every session to set discovery targets. Update it at least weekly during the Friday ritual.

## Verify

- Launching Obsidian opens `spaces/inbox.md`
- Clicking **Library**, **Knowledge**, or **Project** in the space nav row opens that space in the active tab
- Opening `home.md` from the vault root shows a fallback link to Inbox
- Clicking **Capture fleeting** opens the QuickAdd capture prompt

## Related

- Why the launch surface is a plain note, not a custom app: [Home — the vault front door](../../explanation/obsidian/home.md)
- The persistent gate decision: [ADR-81](../../adr/81-persistent-gate-dashboards.md)
- What each dashboard shows: [explanation/dashboards/](../../explanation/dashboards)
- The reset workspace: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- Updating research focus on schedule: [Run the weekly review](../inbox/run-the-weekly-review.md)
