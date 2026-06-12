---
title: Navigate the dashboards
parent: Using Obsidian
nav_order: 5
---

# Navigate the dashboards

Each dashboard in `system/dashboards/` answers one question about the vault, and a healthy vault shows them near-empty. This guide maps situations to dashboards — open the right one first. For the full roster and what each one shows, see [Dashboards](../../reference/dashboards.md).

## Where the dashboards open

The two shipped workspaces pre-load the highest-frequency views ([Workspaces](use-workspaces.md)):

| Workspace | Pre-loaded |
| --- | --- |
| **Home** (default) | `home.md` (status glance + the Inbox queue) in the main pane, Board State on the right |
| **Library** | Reading Pipeline + Discuss Queue + `catalog.base` as left-pane tabs |

Everything else opens manually: the grouped links on `home.md`, or `Cmd/Ctrl-P` → Omnisearch → the dashboard name.

---

## Situation → dashboard

### "What needs attention right now?"

**The homepage glance + What needs me** — load the Home workspace.

Glance at the start of every session. Empty means nothing urgent; under 30 seconds to read.

### "What work is in flight? What's stuck?"

**Board State** — Home workspace, right pane.

A card sitting in one lane for days is likely stuck: [Fix a stuck card](../troubleshooting/fix-stuck-card.md).

### "What should I read and distill next?"

**Reading Pipeline** — Library workspace, left pane.

Oldest-first — clear the oldest items first. See [Classify a source](../compile/classify-a-source.md).

### "Which papers are worth a discussion pass?"

**Discuss Queue** — Library workspace, left pane.

Open a paper from this queue, then open the Agent Client pane — the active note auto-attaches. See [Discuss a paper](../compile/discuss-a-paper.md).

### "What open questions has my synthesis raised?"

**Open Questions** — open manually.

Review during the weekly review or when starting a new topic cluster — connect each unconnected claim to a hub or to related claims.

### "Are any of my claims contradicted by other claims?"

**Contradictions** — open manually.

Check before advancing a claim to `evergreen` or submitting a draft — unresolved contradictions mean the argument isn't settled.

### "Something seems wrong but I can't see why"

**Drift Watch** — open manually.

Open when agents behave unexpectedly or queries return wrong results. A FAIL verdict pauses scheduled work until resolved ([Run the Linter](../operate/run-the-linter.md)).

### "Are my agents performing well? Is API cost increasing?"

**Fleet Health** — open manually.

Check monthly or when a lane seems slow or degraded. Not for daily use — meaningful only after a week or more of accumulated data.

### "What did the policy MCP allow or deny?"

**Audit Log** — open manually.

Open when a write didn't happen as expected ([Diagnose a denied or blocked write](../troubleshooting/diagnose-a-denied-write.md)), or after a lane-override change to confirm the new policy behaves as intended.

### "What do I need to do this week?"

**Weekly Review** — open on Fridays.

The [Run the weekly review](../curate/run-the-weekly-review.md) guide walks through it step by step.

### "What low-stakes structural debt has piled up?"

**Loose Ends** — open during the weekly review or after a lint pass.

More than five items is a cleanup signal.

## Related

- Weekly review procedure: [Run the weekly review](../curate/run-the-weekly-review.md)
- Workspace layouts: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- The dashboard inventory and the Bases views behind it: [Dashboards](../../reference/dashboards.md)
