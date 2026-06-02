---
title: How to use the vault homepage
parent: Using Obsidian
---

# How to use the vault homepage

The obsidian-homepage plugin opens the `Home.md` front-door note on launch ([ADR-13](../../../project-files/decisions/13-homepage-front-door.md)); it links straight to `00-meta/start-here.md`, the pinned landing page. Navigate from there to the right dashboard or tool, and update your research directions so the Librarian has targets at session start.

## Prerequisites

- The vault open in Obsidian
- The **Human** workspace loaded (`Cmd/Ctrl-1`) — the homepage opens in the left pane by default

## Steps

**1. Open the homepage.**

The obsidian-homepage plugin opens `Home.md` automatically on launch; follow its link to `00-meta/start-here.md` — the pinned landing page this guide works from. If neither is visible:

- `Cmd/Ctrl-P` → **Open default note** (opens `Home.md`)
- Or navigate manually: file explorer → `00-meta` → `start-here.md`

Pin it in the sidebar so it's always one click away: right-click the tab → **Pin**.

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

**3. Update your research directions.**

The Librarian reads `00-meta/research-directions.md` at the start of every session to set discovery targets. Keep it current.

Click **Research directions** in the homepage → edit the file directly:

- **Current priorities** — up to 3–5 active research questions
- **Open questions** — specific unresolved questions to surface sources for
- **Synthesis gaps** — topics where your claim notes feel thin
- **Papers to prioritize** — specific papers to front-queue

Update this at least weekly during the Friday ritual.

**4. Run a command from the homepage.**

The **Common operations** section lists the Memoria command-palette shortcuts. Use them directly from here — no need to have a note open first:

- `Cmd/Ctrl-P` → `Memoria: capture fleeting` — instant capture
- `Cmd/Ctrl-P` → `Memoria: new project` — scaffold a project folder

## Verify

- `Cmd/Ctrl-1` (Human workspace) shows the homepage in the left pane
- Clicking **Daily Health** opens `00-meta/01-dashboards/daily-health.md`
- `research-directions.md` has at least one current priority filled in

## Related

- Why the homepage is a consumer, not a producer: [explanation/obsidian/home.md](../../explanation/obsidian/home.md)
- What each dashboard shows: [explanation/dashboards/](../../explanation/dashboards/)
- Workspace layout for the Human workspace: [reference/obsidian-workspaces.md](../../reference/obsidian-workspaces.md)
- Updating research directions on schedule: [how-to-guides/maintenance/run-the-weekly-review.md](../maintenance/run-the-weekly-review.md)
