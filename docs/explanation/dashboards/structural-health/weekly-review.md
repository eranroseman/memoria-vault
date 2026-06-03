---
title: The weekly-review dashboard
parent: Structural health
nav_order: 3
grand_parent: Dashboards
---


# The weekly-review dashboard

The weekly-review dashboard is the Friday-ritual entry point. Open it at the start of each weekly session and work top to bottom: clear the inbox, decide on discovery candidates, promote evergreen claim notes, check orphans, review project pages, glance at metrics. The discipline is **one ritual per week, ~90 minutes** — not "open whenever." A weekly cadence is what prevents the vault from accumulating drift faster than it produces synthesis.

---

## What this dashboard is not

**Not [Daily Health](../daily-glance/daily-health.md).** Daily Health is the morning health glance — 30 seconds, system signals, close if green. Weekly review is the knowledge ritual — 90 minutes, deliberate human decisions about content. Different rhythm, different scope, different cognitive mode.

**Not the only weekly view.** The `reading-pipeline`, `loose-ends`, and `drift-watch` dashboards are also recommended-weekly — but weekly-review is the ritual *entry point* that links to them and defines the order. It is the orchestrator of the weekly ritual, not just one surface among several.

**Not auto-actioned.** Every section requires a human decision: promote or defer, archive or keep, include or exclude. Nothing in this dashboard is triggered by a cron job. The human is the agent of all state changes it surfaces.

---

## Why it's designed this way

**Top-to-bottom ordering follows the workflow logic.** Inbox review unblocks downstream synthesis, so it comes first. Promotion comes before metrics because the metrics reflect promotion behavior — reviewing metrics before doing the promotions would show stale numbers. The sequence is not aesthetic; it is causal.

**Empty sections are the goal, not a bug.** A healthy week leaves most sections empty. The discipline is recognizing empty as success rather than a sign that the dashboard isn't working.

**The orphan check has a coverage angle.** Beyond the raw orphan count (notes with zero inbound links), the check surfaces qualifying notes that should connect to current work but don't. This catches missing coverage, not just disconnected notes — the difference between a note that genuinely stands alone and a note that should be connected but hasn't been.

**Schema migration progress lives elsewhere.** Structural maintenance (schema drift, plugin config changes) belongs in `drift-watch`, not here. Weekly-review surfaces content decisions; mixing structural maintenance into the same ritual crowds the human's Friday attention with two different cognitive tasks.

---

## Related

**Explanation**

- Dashboard opened first thing every morning: [Daily Health](../daily-glance/daily-health.md)
- Reading-stage companion: [The reading-pipeline dashboard](../synthesis-agenda/reading-pipeline.md)
- Why the ritual matters: [The knowledge cycle](../../knowledge/knowledge-cycle.md)
- The dashboards overview: [Dashboards](../README.md)

**How-to**

- How to run the ritual: [run the weekly review](../../../how-to-guides/maintenance/run-the-weekly-review.md)

**Background**

- Structural drift companion: `drift-watch`
