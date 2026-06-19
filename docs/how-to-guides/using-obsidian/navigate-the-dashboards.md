---
title: Navigate the dashboards
parent: Using Obsidian
nav_order: 5
---

# Navigate the dashboards

Each space dashboard under `spaces/` gathers the views for one working mode, and the supporting dashboards under `system/dashboards/` answer narrower operational questions. This guide maps situations to the right surface. For the full roster and what each one shows, see [Dashboards](../../reference/dashboards.md).

## Where the dashboards open

The shipped spaces — **Inbox**, **Library**, **Knowledge**, and **Project** — are dashboard notes with a nav row. The Homepage plugin opens Inbox on startup; use the nav row to move among spaces. The saved **Memoria** workspace is only a reset layout; see [Use the reset workspace](use-workspaces.md).

Everything else opens manually: follow links from a space dashboard, or use `Cmd/Ctrl-P` → Omnisearch → the dashboard name.

---

## Situation → dashboard

### "What needs attention right now?"

**Inbox** — `spaces/inbox.md`.

Glance at the start of every session. Empty means nothing urgent; under 30 seconds to read.

### "What work is in flight? What's stuck?"

**Inbox** — Board section.

A card sitting in one lane for days is likely stuck: [Fix a stuck card](../troubleshooting/fix-stuck-card.md).

### "What should I read and distill next?"

**Library** — `spaces/library.md`.

Oldest-first — clear the oldest items first. See [Classify a source](../library/classify-a-source.md).

### "Which papers are worth a discussion pass?"

**Discuss queue** — Library space.

Open a paper from this queue, then open the Agent Client pane — the active note auto-attaches. See [Discuss a paper](../library/discuss-a-paper.md).

### "What open questions has my synthesis raised?"

**Open questions** — Knowledge space.

Review during the weekly review or when starting a new topic cluster — connect each unconnected claim to a hub or to related claims.

### "Are any of my claims contradicted by other claims?"

**Contradictions** — Knowledge space.

Check before advancing a claim to `evergreen` or submitting a draft — unresolved contradictions mean the argument isn't settled.

### "Is this project ready to draft?"

**Project** — `spaces/project.md`.

Refresh the gate from a project file, then read the active thesis, refutation stamp,
graph maturity, saturation state, and gap findings.

### "Something seems wrong but I can't see why"

**Drift watch** — Inbox space.

Open when agents behave unexpectedly or queries return wrong results. A FAIL verdict pauses scheduled work until resolved ([Run the Linter](../operate/run-the-linter.md)).

### "Are my agents performing well? Is API cost increasing?"

**Fleet Health** — open manually.

Check monthly or when a lane seems slow or degraded. Not for daily use — meaningful only after a week or more of accumulated data.

### "What did the policy MCP allow or deny?"

**Audit Log** — open manually.

Open when a write didn't happen as expected ([Diagnose a denied or blocked write](../troubleshooting/diagnose-a-denied-write.md)), or after a lane-override change to confirm the new policy behaves as intended.

### "What do I need to do this week?"

**Weekly review** — open manually on Fridays.

The [Run the weekly review](../inbox/run-the-weekly-review.md) guide walks through it step by step.

### "What low-stakes structural debt has piled up?"

**Loose Ends** — open during the weekly review or after a lint pass.

More than five items is a cleanup signal.

## Related

- Weekly review procedure: [Run the weekly review](../inbox/run-the-weekly-review.md)
- Workspace layouts: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- The dashboard inventory and the Bases views behind it: [Dashboards](../../reference/dashboards.md)
