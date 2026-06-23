---
title: Navigate the dashboards
parent: Using Obsidian
nav_order: 5
---

# Navigate the dashboards

Memoria has a few different surfaces, and it is easy to lose track of which one answers which question. This guide maps everyday situations to the exact place to look.

You move around Memoria from the **navigator rail** on the left. It has two parts:

- **Now** — what is waiting for you right now. Three entries: **Needs you** (your action queue), **Drift** (integrity flags), and **Fleet** (the health of the background workers).
- **Places** — the three working **spaces** you switch between: **Library** (sources you are reading), **Knowledge** (claims you are synthesizing), and **Project** (drafts you are steering toward output).

Two more surfaces hang off *Now*. The **Inbox** is your action queue — open it from *Now → Needs you*; its main view is **Needs me**. **Maintenance** is a separate weekly surface for structural cleanup; it holds Drift watch, Loose ends, the Board, and a "new this week" digest.

Behind those surfaces sit **5 read-only system dashboards** under `system/dashboards/`. They are Dataview-backed views that report state and never change anything. The space surfaces themselves are built from Obsidian Bases (database-style views over your notes). For the full roster and what each one shows, see [Dashboards](../../reference/dashboards.md).

A few orientation notes: startup restores the saved **Memoria** shell, but you still navigate through the left rail, not by switching saved workspaces; see [Use the reset workspace](use-workspaces.md). `home.md` is a launch screen, not a navigation hub, so do not treat it as your home base.

To open anything that is not on the rail, follow a link from a space, or press `Cmd/Ctrl-P` → Omnisearch → the dashboard name.

---

## Situation → where to look

### "What needs attention right now?"

Open the **Inbox** (`spaces/inbox.md`) from *Now → Needs you*.

The Inbox is your action queue: items that Memoria has parked for a decision from you. Glance at it at the start of every session. Empty means nothing is waiting; a full read takes under 30 seconds.

### "What work is in flight? What's stuck?"

Open **Maintenance** from *Now*, then read its **Board** section.

The Board shows the background workers — Memoria calls them **lanes** — and the work moving through them as **cards** (one card per unit of work). A card that has sat in the same lane for days is probably stuck: [Fix a stuck card](../troubleshooting/fix-stuck-card.md).

### "What should I read and distill next?"

Open the **Library** space (`spaces/library.md`) from *Places*.

Library is where sources you are reading live. It lists items oldest-first, so clear the oldest ones first. See [Classify a source](../library/classify-a-source.md).

### "Which papers are worth a discussion pass?"

Open the **Library** space, then its **Discuss queue** view.

This queue lists papers ready for a back-and-forth with the conversational agent (the **Co-PI**). Open a paper from the queue, then open the Agent Client pane — the active note attaches itself automatically. See [Discuss a paper](../library/discuss-a-paper.md).

### "What open questions has my synthesis raised?"

Open the **Knowledge** space, then its **Open questions** view.

Knowledge is where your **claims** live — the individual statements you are building an argument from. A **hub** is a topic note that gathers related claims in one place. Review Open questions during the weekly review, or when starting a new topic cluster, and connect each loose claim either to a hub or to related claims.

### "Are any of my claims contradicted by other claims?"

Open the **Knowledge** space, then its **Contradictions** view.

This view lists pairs of claims that disagree with each other. Check it before you promote a claim to `evergreen` (the most settled maturity level) or submit a draft. An unresolved contradiction means the argument is not settled yet.

### "Is this project ready to draft?"

Open the **Project** space (`spaces/project.md`) from *Places*.

Project steers a piece of work toward output. Refresh it from a project file, then read the project's readiness signals: the active thesis, the **refutation stamp** (a record of whether the thesis survived being argued against), how mature the claim graph is, the **saturation** state (whether new sources are still adding anything, or you have read enough), and any remaining gap findings.

### "Something seems wrong but I can't see why"

Open **Maintenance** from *Now*, then read its **Drift watch** view. You can also reach drift flags directly from *Now → Drift*.

Drift watch flags integrity problems — the kind of thing that makes agents behave oddly or queries return wrong results. It shows a `PASS` / `REVIEW` / `FAIL` band. A `FAIL` pauses scheduled work until you resolve it ([Run the Linter](../operate/run-the-linter.md)).

### "Are my workers performing well? Is API cost increasing?"

Open **Fleet health** (`system/dashboards/fleet-health.md`), reachable from *Now → Fleet*.

This dashboard scores each lane (background worker) on trust and cost. Check it monthly, or when a lane seems slow or degraded. It is not a daily surface — the numbers only mean something after a week or more of accumulated data.

### "What did the policy MCP allow or deny?"

Open the **Audit log** (`system/dashboards/audit-log.md`) manually.

This dashboard lists recent writes and whether the policy layer allowed or denied each one. Open it when a write did not happen as you expected ([Diagnose a denied or blocked write](../troubleshooting/diagnose-a-denied-write.md)), or after changing a lane's policy override to confirm the new rule behaves as intended.

### "What do I need to do this week?"

Open **Maintenance** from *Now* on Fridays for the weekly review.

Maintenance gathers the week's structural cleanup in one place. The [Run the weekly review](../inbox/run-the-weekly-review.md) guide walks through it step by step.

### "What low-stakes structural debt has piled up?"

Open **Maintenance** from *Now*, then read its **Loose ends** view.

Loose ends collects small structural tidy-ups that are safe to defer. More than five items waiting is a signal to do a cleanup pass.

## Related

- Weekly review procedure: [Run the weekly review](../inbox/run-the-weekly-review.md)
- Workspace layouts: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- The dashboard inventory and the Bases views behind it: [Dashboards](../../reference/dashboards.md)
