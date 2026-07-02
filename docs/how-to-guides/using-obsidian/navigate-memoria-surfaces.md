---
title: Navigate Memoria surfaces
parent: Using Obsidian
grand_parent: How-to guides
nav_order: 5
---

# Navigate Memoria surfaces

Memoria has a few different surfaces, and it is easy to lose track of which one answers which question. This guide maps everyday situations to the exact place to look.

You move around Memoria from the **navigator rail** on the left: **Now** for the daily action queue and health links, **Places** for Library, Knowledge, and Project. The full dashboard inventory is [Dashboards](../../reference/dashboards.md); this page only tells you where to go for common situations.

Startup preserves Obsidian's previous session when the rail is present, and uses the saved **Memoria** shell only to repair a missing rail; see [Use the reset workspace](reset-workspace.md). You still navigate through the left rail, not by switching saved workspaces. `home.md` is a reset/welcome screen, not a navigation hub.

To open anything that is not on the rail, follow a link from a space, or press `Cmd/Ctrl-P` → Omnisearch → the dashboard name.

---

## Situation → where to look

### "What needs attention right now?"

Open the **Inbox** (`spaces/inbox.md`) from *Now → Action queue*.

The Inbox answers two quick questions: what is currently queued or running, and what action needs you now. Glance at Activity first, then work **Needs me** if it has rows. Empty means nothing is waiting; a full read takes under 30 seconds.

### "What work is in flight? What's stuck?"

For a quick live answer, read **Inbox → Activity**. For blocked, done, or older board history, open **Maintenance** from *Now*, then read its **Board** section.

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

This view lists pairs of claims that disagree with each other. Check it before you advance a claim's maturity to `evergreen` (the most settled level) or submit a draft. An unresolved contradiction means the argument is not settled yet.

### "Is this project ready to draft?"

Open the **Project** space (`spaces/project.md`) from *Places*.

Project steers a piece of work toward output. Refresh it from a project file, then read the project's readiness signals: the active thesis, the **refutation stamp** (a record of whether the thesis survived being argued against), how mature the claim graph is, the **saturation** state (whether new sources are still adding anything, or you have read enough), and any remaining gap findings.

### "Something seems wrong but I can't see why"

Open **Maintenance** from *Now*, then read its **Drift watch** view. You can also reach drift flags directly from *Now → Drift*.

Drift watch flags integrity problems — the kind of thing that makes agents
behave oddly or queries return wrong results. It shows a `PASS` / `REVIEW` /
`FAIL` band. A `FAIL` blocks new delegation or worker promotion until the
blocking finding is acknowledged or resolved ([Run the Linter](../operate/run-the-linter.md)).

### "Are my workers performing well? Is API cost increasing?"

Open **Fleet health** (`system/dashboards/fleet-health.md`), reachable from *Now → Fleet*.

This dashboard scores each lane (background worker) on trust and cost. Check it monthly, or when a lane seems slow or degraded. It is not a daily surface — the numbers only mean something after a week or more of accumulated data.

### "What did the policy gate allow or deny?"

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
