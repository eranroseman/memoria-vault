---
title: Vault homepage
parent: Using Obsidian
nav_order: 1
---

# Vault homepage

The obsidian-homepage plugin opens `home.md` — the vault-root front door — on launch ([ADR-13](../../adr/13-homepage-front-door.md)). It's a launchpad: a one-line status glance, then links to every dashboard, the in-vault troubleshooting note, common operations, and the full website docs (all other reference now lives on the website). Navigate from it to the right dashboard or tool, and keep your research focus current.

## Prerequisites

- The vault open in Obsidian
- The **Human** workspace loaded (`Cmd/Ctrl-1`) — the homepage opens in the left pane by default

## Steps

**1. Open the homepage.**

The obsidian-homepage plugin opens `home.md` automatically on launch (in Reading view, Dataview refreshed). If it isn't visible:

- `Cmd/Ctrl-P` → **Homepage: Open homepage**, or click the home ribbon icon
- Or open `home.md` from the vault root in the file explorer

To get back to a clean homepage view at any time, **right-click a tab header → Close all** — it closes every open tab and re-launches the homepage.

The plugin pins the tab for you (configurable); you can also right-click the tab → **Pin**.

**2. Navigate to a dashboard.**

The homepage links to all dashboards without duplicating their queries. Click any link to open it:

| Link | Opens |
| --- | --- |
| **Daily Health** | System-health view — board queues, drift signals, cron status |
| **Reading queue** | Papers classified but not yet discussed or distilled |
| **Weekly ritual** | Friday vault-state audit |
| **Board state** | Full Kanban board |
| **Audit log** | Per-decision forensics from the policy MCP |
| **Drift watch** | Linter findings and verdict band |

**3. Update your research focus.**

The Librarian reads `research-focus.md` at the start of every session to set discovery targets. Keep it current.

Click **Research focus** in the homepage → edit the file directly:

- **Current priorities** — up to 3–5 active research questions
- **Open questions** — specific unresolved questions to surface sources for
- **Synthesis gaps** — topics where your claim notes feel thin
- **Papers to prioritize** — specific papers to front-queue

Update this at least weekly during the Friday ritual.

**4. Run a command from the homepage.**

The **Common operations** section lists the Memoria command-palette shortcuts. Use them directly from here — no need to have a note open first:

- `Cmd/Ctrl-P` → `Memoria: capture fleeting` — instant capture
- `Cmd/Ctrl-P` → `Memoria: write claim note` — start a new claim from the template

## Verify

- `Cmd/Ctrl-1` (Human workspace) shows the homepage in the left pane
- Clicking **Daily Health** opens `00-meta/01-dashboards/daily-health.md`
- `research-focus.md` has at least one current priority filled in

## Related

- Why the homepage is a consumer, not a producer: [Home — the vault front door](../../explanation/obsidian/home.md)
- What each dashboard shows: [explanation/dashboards/](../../explanation/dashboards)
- Workspace layout for the Human workspace: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- Updating research focus on schedule: [Run the weekly review](../curate/run-the-weekly-review.md)
