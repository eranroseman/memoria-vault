---
title: The Daily Health dashboard
parent: Daily glance
nav_order: 1
grand_parent: Dashboards
---

# The Daily Health dashboard

> **Absorbed into Home.** Daily Health no longer exists as a standalone dashboard file — the design update folded it into **`home.md`**, the front door. Its job (the morning "is anything red?" glance) is now the homepage's one-line **status strip**, with the Inbox's "what needs me?" view one click away in the Desk workspace ([ADR-68](../../../adr/68-workspaces-desk-library-studio.md)), so the daily ritual starts on the surface Obsidian already opens. This page records the design rationale, which survives the move unchanged.

The daily health view is the always-on system glance. The budget is 30 seconds — glance, decide whether anything is red, close. If nothing is red, move on to real work.

---

## What it shows

Home's status strip is a one-line rollup read from the telemetry feeds in `system/logs/`: pending reviews and blocked cards (from the board-state snapshot) and HIGH/CRITICAL lint findings. In the Desk workspace, the **"Needs me"** view of the Inbox board lists the cards in `proposed` — the things actually waiting on a decision. Each is an "is anything red?" check, not a place to do work — the deeper dashboards (board-state, drift-watch, fleet-health) are where you act.

---

## What this surface is not

**Not a vault audit.** Folder counts, orphan notes, stale literature — those are the weekly review's job. The daily glance is *system health*, not *knowledge health*. Mixing them would turn a 30-second glance into a 20-minute triage session.

**Not a task list.** It shows decisions waiting on the human; the human chooses which to address. The Inbox cards, not the glance line, are where state changes happen.

**Not a substitute for the deeper dashboards.** It summarizes red signals; the full views live in `drift-watch`, `fleet-health`, and `audit-log`. It is a dashboard-of-dashboards: filtered subsets of those deeper views, reached by clicking through.

---

## Why it's designed this way

**Absorption beats a second front door.** A standalone Daily Health page was one more thing to open every morning — and a launchpad that owns no logic can't drift or error. The consumer-only, degrades-to-empty rationale for folding the glance into the front door is owned by [Home — the vault front door](../../obsidian/home.md); the upshot here is that the glance is always exactly as fresh as its feeds.

**Graded loudness decides what reaches it.** `alert`- and `block`-level findings surface in the above-fold glance; quieter findings stay in the relevant dashboard or are logged only. Alert/block cards also record Telegram push attempts when written through the shared card writer, and open block cards pause new delegation plus review-gated promotion until resolved. The four-level loudness model and the "does it change what the PI does in the next 30 minutes?" test it turns on are owned by [Interaction channels](../../architecture/human-channels.md).

**Graceful degradation.** When a feed has no data yet — a fresh vault with no agent runs — the glance states what would populate it: empty means "nothing to report," not "something is broken" (the cross-cutting [graceful-degradation principle](../README.md#why-the-dashboards-are-designed-the-way-they-are)).

**30 seconds is a constraint, not an aspiration.** A daily ritual that consistently takes more than 30 seconds stops being daily. A healthy vault produces an all-clear line and an empty "Needs me" view, and the human closes it immediately. Length is a signal: a long glance means something needs attention, not that the ritual needs more time allocated.

---

## Related

- The board behind "Needs me": [The board-state dashboard](board-state.md)
- The weekly-ritual companion: [The weekly-review dashboard](../structural-health/weekly-review.md)
- What populates the drift signals: [drift-watch dashboard](../structural-health/drift-watch.md)
- What populates the trust scores: [fleet-health dashboard](../operational-health/fleet-health.md)
