---
title: Vault homepage
parent: Using Obsidian
nav_order: 1
---

# Vault homepage

The obsidian-homepage plugin opens `home.md` — the vault-root front door — on launch ([ADR-13](../../adr/13-homepage-front-door.md)). It's a launchpad: a one-line status glance, then links to every dashboard, the in-vault troubleshooting note, common operations, and the full website docs (all other reference now lives on the website). Navigate from it to the right dashboard or tool, and keep your research focus current.

## Prerequisites

- The vault open in Obsidian
- The **Home** workspace loaded — the homepage sits front and center in its main pane ([Workspaces](use-workspaces.md))

## Steps

**1. Open the homepage.**

The obsidian-homepage plugin opens `home.md` automatically on launch (in Reading view, Dataview refreshed). If it isn't visible:

- `Cmd/Ctrl-P` → **Homepage: Open homepage**, or click the home ribbon icon
- Or open `home.md` from the vault root in the file explorer

To get back to a clean homepage view at any time, **right-click a tab header → Close all** — it closes every open tab and re-launches the homepage.

The plugin pins the tab for you (configurable); you can also right-click the tab → **Pin**.

**2. Read the glance, then work the Inbox.**

Above the fold the homepage carries the **Status glance** (reviews pending · blocked cards · HIGH/CRITICAL lint findings) and **What needs me** — the Inbox cards in `proposed`, embedded from `inbox.base`. That queue converges to empty; everything below is on-demand detail.

**3. Navigate to a dashboard.**

The homepage links to every dashboard without duplicating their queries, in three groups by how you use them — **Library** (reading & synthesis), **Maintenance** (structural health), and **Agent ops**. For the full roster and what each one shows, see [Dashboards](../../reference/dashboards.md); to pick the right one for a situation, see [Navigate the dashboards](navigate-the-dashboards.md).

**4. Update your research focus.**

The Librarian reads `research-focus.md` at the start of every session to set discovery targets. Keep it current.

Click **Research focus** in the homepage → edit the file directly:

- **Current priorities** — up to 3–5 active research questions
- **Open questions** — specific unresolved questions to surface sources for
- **Synthesis gaps** — topics where your claim notes feel thin
- **Papers to prioritize** — specific papers to front-queue

Update this at least weekly during the Friday ritual.

**5. Start work from the homepage.**

The **Start here** section is the launchpad for a session — no need to have a note open first:

- **Research focus** — open and refresh `research-focus.md`
- **Talk to the co-PI** — `Agent Client: Open chat view` ([Agent-client pane](use-the-acp-pane.md))
- `Cmd/Ctrl-P` → `Memoria: capture fleeting` — instant capture

## Verify

- Loading the **Home** workspace shows the homepage front and center, with the Status glance rendered (or its "feeds not wired yet" placeholder before the first agent run)
- Clicking **Board State** opens `system/dashboards/board-state.md`
- `research-focus.md` has at least one current priority filled in

## Related

- Why the homepage is a consumer, not a producer: [Home — the vault front door](../../explanation/obsidian/home.md)
- What each dashboard shows: [explanation/dashboards/](../../explanation/dashboards)
- Workspace layout for the Home workspace: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- Updating research focus on schedule: [Run the weekly review](../curate/run-the-weekly-review.md)
