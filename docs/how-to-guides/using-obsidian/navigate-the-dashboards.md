---
title: Navigate the dashboards
parent: Using Obsidian
nav_order: 5
---

# Navigate the dashboards

Each dashboard in `system/dashboards/` answers one question about the vault, and a healthy vault shows them near-empty. This guide maps situations to dashboards — open the right one first. For the full roster and what each one shows, see [Dashboards](../../reference/dashboards.md).

## Where the dashboards open

The three shipped workspaces — **Desk** (the board and Inbox), **Library** (the reading pipeline and catalog), and **Studio** (drafting plus the Project gate) — each pre-load the highest-frequency views for their mode. For the exact main-pane dashboard and left tabs each one loads, see the layout table in [Obsidian workspaces](../../reference/obsidian-workspaces.md); to switch between them, see [Workspaces](use-workspaces.md).

Everything else opens manually: the grouped links on `home.md`, or `Cmd/Ctrl-P` → Omnisearch → the dashboard name.
For project work, `Memoria: open Project gate` loads Studio and opens `project-gate.md`
directly.

---

## Situation → dashboard

### "What needs attention right now?"

**The homepage status strip, then the Desk workspace** — the board and the Inbox queue side by side.

Glance at the start of every session. Empty means nothing urgent; under 30 seconds to read.

### "What work is in flight? What's stuck?"

**Desk** — Desk workspace, main pane.

A card sitting in one lane for days is likely stuck: [Fix a stuck card](../troubleshooting/fix-stuck-card.md).

### "What should I read and distill next?"

**Library** — Library workspace, main pane.

Oldest-first — clear the oldest items first. See [Classify a source](../compile/classify-a-source.md).

### "Which papers are worth a discussion pass?"

**Discuss Queue** — Library workspace, left tab.

Open a paper from this queue, then open the Agent Client pane — the active note auto-attaches. See [Discuss a paper](../compile/discuss-a-paper.md).

### "What open questions has my synthesis raised?"

**Open Questions** — Library workspace, left tab.

Review during the weekly review or when starting a new topic cluster — connect each unconnected claim to a hub or to related claims.

### "Are any of my claims contradicted by other claims?"

**Contradictions** — Library workspace, left tab.

Check before advancing a claim to `evergreen` or submitting a draft — unresolved contradictions mean the argument isn't settled.

### "Is this project ready to draft?"

**Project Gate** — `Memoria: open Project gate`, inside Studio.

Refresh the gate from a project file, then read the active thesis, refutation stamp,
graph maturity, saturation state, and gap findings.

### "Something seems wrong but I can't see why"

**Drift Watch** — Desk workspace, left tab.

Open when agents behave unexpectedly or queries return wrong results. A FAIL verdict pauses scheduled work until resolved ([Run the Linter](../operate/run-the-linter.md)).

### "Are my agents performing well? Is API cost increasing?"

**Fleet Health** — open manually.

Check monthly or when a lane seems slow or degraded. Not for daily use — meaningful only after a week or more of accumulated data.

### "What did the policy MCP allow or deny?"

**Audit Log** — open manually.

Open when a write didn't happen as expected ([Diagnose a denied or blocked write](../troubleshooting/diagnose-a-denied-write.md)), or after a lane-override change to confirm the new policy behaves as intended.

### "What do I need to do this week?"

**Weekly Review** — Desk workspace, left tab; open on Fridays.

The [Run the weekly review](../curate/run-the-weekly-review.md) guide walks through it step by step.

### "What low-stakes structural debt has piled up?"

**Loose Ends** — open during the weekly review or after a lint pass.

More than five items is a cleanup signal.

## Related

- Weekly review procedure: [Run the weekly review](../curate/run-the-weekly-review.md)
- Workspace layouts: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- The dashboard inventory and the Bases views behind it: [Dashboards](../../reference/dashboards.md)
