---
title: Navigate the dashboards
parent: Using Obsidian
nav_order: 5
---

# Navigate the dashboards

Ten dashboards in `system/dashboards/`, plus the homepage's above-the-fold glance (the v0.1.0 daily-health dashboard was absorbed into `home.md` — there is no `daily-health.md`). Each dashboard answers one question about the vault; a healthy vault shows them near-empty. This guide maps situations to dashboards — open the right one first.

For what each dashboard shows in detail, see [Dashboards](../../reference/dashboards.md).

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

Glance at the start of every session: reviews pending, blocked cards, HIGH/CRITICAL lint findings, then the Inbox cards in `proposed` waiting on your decision. Empty means nothing urgent. Under 30 seconds to read.

### "What work is in flight? What's stuck?"

**Board State** — Home workspace, right pane.

The Inbox board (embeds `inbox.base`) plus live worker cards from `system/board/`. A card sitting in one lane for days is likely stuck: [Fix a stuck card](../troubleshooting/fix-stuck-card.md).

### "What should I read and distill next?"

**Reading Pipeline** — Library workspace, left pane.

Sources awaiting classification and claims by maturity. Oldest-first — clear the oldest items first. See [Classify a source](../compile/classify-a-source.md).

### "Which papers are worth a discussion pass?"

**Discuss Queue** — Library workspace, left pane.

Read-but-not-distilled sources worth a co-PI pass. Open a paper from this queue, then open the Agent Client pane — the active note auto-attaches. See [Discuss a paper](../compile/discuss-a-paper.md).

### "What open questions has my synthesis raised?"

**Open Questions** — open manually.

Unconnected claims — the synthesis backlog: `current` claims with zero inbound links, that no hub holds and nothing links to yet. Review during the weekly review or when starting a new topic cluster. These are facts the corpus has captured but not yet woven in — connect each to a hub or to related claims.

### "Are any of my claims contradicted by other claims?"

**Contradictions** — open manually.

Every pair of claim notes joined by a **human-set** `contradicts` link. No model judges which claims conflict — the agents may _propose_ a contradiction for confirmation, but the link is always human-set. Check before advancing a claim to `evergreen` or submitting a draft — unresolved contradictions mean the argument isn't settled.

### "Something seems wrong but I can't see why"

**Drift Watch** — open manually.

Verdict band at the top: PASS / REVIEW / FAIL ([Run the Linter](../operate/run-the-linter.md)). FAIL means a CRITICAL structural finding — scheduled work pauses until it's resolved. Open when agents behave unexpectedly or queries return wrong results.

### "Are my agents performing well? Is API cost increasing?"

**Fleet Health** — open manually.

Per-lane trust score and operational rollup from `system/metrics/`. Check monthly or when a lane seems slow or degraded. Not for daily use — meaningful only after a week or more of accumulated data.

### "What did the policy MCP allow or deny?"

**Audit Log** — open manually.

Per-decision forensics over `system/logs/audit.jsonl`. Open when a write didn't happen as expected — the log shows whether it was denied and why ([Diagnose a denied or blocked write](../troubleshooting/diagnose-a-denied-write.md)). Also useful after any lane-override change to confirm the new policy behaves as intended.

### "What do I need to do this week?"

**Weekly Review** — open on Fridays.

The Friday aggregator: classify backlog, outstanding discovery candidates, drift-watch verdict, retraction candidates. The [Run the weekly review](../curate/run-the-weekly-review.md) guide walks through it step by step.

### "What low-stakes structural debt has piled up?"

**Loose Ends** — open during the weekly review or after a lint pass.

Structural debt batched at Notice loudness: `flag` cards in `proposed` with `loudness = notice` — cosmetic and low-stakes findings the Linter never pushes. More than five is a cleanup signal.

---

## Quick reference

| Dashboard | When to open | Where |
| --- | --- | --- |
| Homepage glance | Start of session | Home workspace |
| Board State | Check for stuck cards | Home workspace, right pane |
| Reading Pipeline | Classify backlog | Library workspace, left pane |
| Discuss Queue | Reading session | Library workspace, left pane |
| Open Questions | Weekly review / new topic | Manual |
| Contradictions | Before evergreen or a draft | Manual |
| Drift Watch | When something seems off | Manual |
| Loose Ends | Weekly review or lint pass | Manual |
| Weekly Review | Fridays | Manual |
| Audit Log | After unexpected write failure | Manual |
| Fleet Health | Monthly check | Manual |

## Related

- Weekly review procedure: [Run the weekly review](../curate/run-the-weekly-review.md)
- Workspace layouts: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- The dashboard inventory and the Bases views behind it: [Dashboards](../../reference/dashboards.md)
