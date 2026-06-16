---
title: Vault homepage
parent: Using Obsidian
nav_order: 1
---

# Vault homepage

The obsidian-homepage plugin opens `home.md` — the vault-root front door — on launch ([ADR-13](../../adr/13-homepage-front-door.md)). Since [ADR-68](../../adr/68-workspaces-desk-library-studio.md) it is a four-block **control panel**: a one-line status strip, an action row of command buttons, a navigation row, and the collapsed drill-down index. Glance, act, navigate — it owns no logic and duplicates no dashboard.

## Prerequisites

- The vault open in Obsidian

## Steps

**1. Open the homepage.**

The obsidian-homepage plugin opens `home.md` automatically on launch (in Reading view, Dataview refreshed). It is pinned in no workspace — it appears on launch and on demand:

- `Cmd/Ctrl-P` → **Homepage: Open homepage**, or click the home ribbon icon
- Or open `home.md` from the vault root in the file explorer

To get back to a clean homepage view at any time, **right-click a tab header → Close all** — it closes every open tab and re-launches the homepage.

**2. Read the status strip.**

One line: reviews pending · blocked cards · HIGH/CRITICAL lint findings, with **board** and **findings** links for drill-down. Before the first agent run it shows the "feeds not wired yet" placeholder. Empty means nothing urgent; under ten seconds to read.

**3. Act from the action row.**

Six command buttons (Buttons plugin, command-type only — [Obsidian plugins](../../reference/obsidian-plugins.md)): **Capture fleeting**, **Capture from Zotero**, **Capture URL**, **Delegate a task**, **Resolve card**, and **Talk to Co-PI**. Each dispatches the matching palette command — the buttons are shortcuts, not a second mechanism.

**4. Navigate from the navigation row.**

Three buttons — **Desk** · **Library** · **Studio** — load the matching layout ([Workspaces](use-workspaces.md)). **Project gate** loads Studio and opens the Project gate dashboard inside it. Work happens in the workspaces; the homepage is the hallway between them.

**5. Drill down from the index.**

Collapsed callouts group every dashboard by how you use it — Project, Library, Desk, Maintenance, and Agent ops — plus links to your research focus and the in-vault troubleshooting note. For the full dashboard roster see [Dashboards](../../reference/dashboards.md); to pick the right one for a situation, see [Navigate the dashboards](navigate-the-dashboards.md).

Keep `research-focus.md` current — the Librarian reads it at the start of every session to set discovery targets. Update it at least weekly during the Friday ritual.

## Verify

- Launching Obsidian opens `home.md` with the status strip rendered (or its "feeds not wired yet" placeholder before the first agent run)
- Clicking the **Desk** button loads the Desk workspace with the board front and center
- Clicking **Project gate** opens the Project gate dashboard inside Studio
- Clicking **Capture fleeting** opens the QuickAdd capture prompt

## Related

- Why the homepage is a consumer, not a producer: [Home — the vault front door](../../explanation/obsidian/home.md)
- The control-panel redesign decision: [ADR-68](../../adr/68-workspaces-desk-library-studio.md)
- What each dashboard shows: [explanation/dashboards/](../../explanation/dashboards)
- The workspaces the buttons load: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- Updating research focus on schedule: [Run the weekly review](../curate/run-the-weekly-review.md)
