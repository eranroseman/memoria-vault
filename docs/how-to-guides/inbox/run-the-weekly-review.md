---
title: Run the weekly review
parent: Inbox
grand_parent: How-to guides
nav_order: 4
---

# Run the weekly review

Walk the Friday ritual: refresh your steering, sweep the Inbox, use Maintenance's weekly sections, and check structural health. Allow up to ~60 minutes; closer to 20–30 once the vault is established and the queues run near-empty — **empty is success**.

## Prerequisites

- Obsidian open with the vault
- `spaces/maintenance.md` open — the Friday collection: loose ends, drift watch, board state, and the week's new catalog entries and notes

## Steps

**Step 1 — Refresh research priorities (2 min).**

Open `steering.md`. Confirm or update the active questions and reading focus — the Librarian reads this to aim discovery, and it sets the lens for every decision below.

**Step 2 — Sweep the Inbox (10–15 min).**

Open the Inbox queue's **Needs me** view of `inbox/inbox.base` and work the proposed action cards as one batch: candidates kept or skipped, gaps turned into discovery tasks or archived, and work prompts dismissed once no action remains ([Work the action queue](../inbox/work-the-action-queue.md)). The weekly review is the backstop that keeps the queue from aging past a week.

**Step 3 — Notice-level findings (5 min).**

Maintenance's **Loose ends** view lists cards at `loudness: notice` — things that didn't demand attention mid-week. Resolve each or consciously defer.

**Step 4 — Review the week's movement (5–10 min).**

The **New this week** sections list catalog entries and notes created in the last 7 days. Scan for anything that landed and stalled: a kept paper with no source note, a source stuck at `proposed`, or a claim with no connections (cross-check Knowledge's **Open questions** view).

**Step 5 — Clear unchecked note backlog (10–15 min).**

Return to the Knowledge space's unchecked notes. Accept, edit, or archive each
one. Target: zero unchecked PI notes older than a week.

**Step 6 — Curate settled clusters (5 min).**

Scan checked notes and digests for clusters with several useful links. Curate
the genuinely settled ones into hubs ([Build a hub](../knowledge/build-a-hub.md)).
Don't create hubs just to clear a queue.

**Step 7 — Check structural health (5 min).**

Use Maintenance's **Drift watch** and **Loose ends** views — the Linter operation's daily 06:00 cron feeds them. Address HIGH findings this session; MEDIUM can wait for a maintenance pass; LOW is aggregated noise until it isn't. To re-check after fixes, run the detectors directly ([Run the Linter](../operate/run-the-linter.md)).

**Step 8 — Glance at fleet health (1 min).**

Use the fleet-health dashboard from the rail health band — per-lane trust scores, refreshed by the Monday metrics cron. Anything under 90 is worth a minute's curiosity; under 70 is a real signal.

## Verify

- The Inbox's **Needs me** view is empty
- No stale unchecked note backlog remains
- No HIGH or CRITICAL finding is outstanding in Maintenance's Drift watch
- `steering.md` reflects what you actually intend to read next week

## Related

- The Inbox discipline: [Work the action queue](../inbox/work-the-action-queue.md)
- The detectors behind Maintenance drift watch: [Run the Linter](../operate/run-the-linter.md)
- The dashboard inventory: [Dashboards](../../reference/dashboards.md)
