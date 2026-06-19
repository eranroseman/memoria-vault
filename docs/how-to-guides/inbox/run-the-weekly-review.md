---
title: Run the weekly review
parent: Inbox
nav_order: 4
---

# Run the weekly review

Walk the Friday ritual: refresh your research focus, sweep the Inbox, work the weekly-review aggregator top to bottom, and check structural health. Allow up to ~60 minutes; closer to 20–30 once the vault is established and the queues run near-empty — **empty is success**.

## Prerequisites

- Obsidian open with the vault
- `system/dashboards/weekly-review.md` open — the Friday aggregator: Notice-level findings, the week's new catalog entries and notes, and the fleeting backlog

## Steps

**Step 1 — Refresh research priorities (2 min).**

Open `research-focus.md`. Confirm or update the active questions and reading focus — the Librarian reads this to aim discovery, and it sets the lens for every decision below.

**Step 2 — Sweep the Inbox (10–15 min).**

Open the Inbox space's **Needs me** view of `inbox/inbox.base` (every card at `lifecycle: proposed`) and work it as one batch: candidates kept or skipped, gaps turned into discovery tasks or archived, flags and alerts acted on and resolved ([Work the review queue](../inbox/work-the-review-queue.md)). The weekly review is the backstop that keeps the queue from aging past a week.

**Step 3 — Notice-level findings (5 min).**

The dashboard's top section lists cards at `loudness: notice` — things that didn't demand attention mid-week. Resolve each or consciously defer.

**Step 4 — Review the week's movement (5–10 min).**

The **New this week** sections list catalog entries and notes created in the last 7 days. Scan for anything that landed and stalled: a kept paper with no source note, a source stuck at `proposed`, a claim with no connections (cross-check `system/dashboards/open-questions.md`).

**Step 5 — Clear the fleeting backlog (10–15 min).**

The dashboard embeds the fleeting **To process** view. Promote, attach, or archive each note — including the week's chat exports ([Triage fleeting notes](../inbox/triage-fleeting-notes.md)). Target: zero notes older than a week.

**Step 6 — Advance settled claims (5 min).**

Scan `system/dashboards/claims.base` for long-stable `budding` claims with several inlinks; advance the genuinely settled ones to `evergreen` and slot them into hubs ([Advance a claim to evergreen](../knowledge/promote-a-claim.md)). Don't advance to clear a queue.

**Step 7 — Check structural health (5 min).**

Open `system/dashboards/drift-watch.md` and `loose-ends.md` — the Linter operation's daily 06:00 cron feeds them. Address HIGH findings this session; MEDIUM can wait for a maintenance pass; LOW is aggregated noise until it isn't. To re-check after fixes, run the detectors directly ([Run the Linter](../operate/run-the-linter.md)).

**Step 8 — Glance at fleet health (1 min).**

`system/dashboards/fleet-health.md` — per-lane trust scores, refreshed by the Monday metrics cron. Anything under 90 is worth a minute's curiosity; under 70 is a real signal.

## Verify

- The Inbox shows nothing at `lifecycle: proposed`
- The fleeting backlog on the dashboard is empty
- No HIGH or CRITICAL finding is outstanding on drift-watch
- `research-focus.md` reflects what you actually intend to read next week

## Related

- The Inbox discipline: [Work the review queue](../inbox/work-the-review-queue.md)
- Fleeting triage in depth: [Triage fleeting notes](../inbox/triage-fleeting-notes.md)
- The detectors behind drift-watch: [Run the Linter](../operate/run-the-linter.md)
- The dashboard inventory: [Dashboards](../../reference/dashboards.md)
