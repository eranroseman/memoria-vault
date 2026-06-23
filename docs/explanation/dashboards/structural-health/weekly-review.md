---
title: Weekly review
parent: Structural health
nav_order: 3
grand_parent: Dashboards
---


# Weekly review

The weekly review is the Friday ritual that keeps the Inbox, Maintenance, and Knowledge views from aging into noise. It gathers the week's accumulated content decisions — a full Inbox, candidate cards awaiting triage, claim maturity to revisit, new catalog entries and notes, and quiet-level findings — into one ordered pass. The discipline is **one ritual per week** — not "open whenever." A weekly cadence is what prevents the vault from accumulating drift faster than it produces synthesis. (For the actionable top-to-bottom sequence, see [run the weekly review](../../../how-to-guides/inbox/run-the-weekly-review.md); the ordering rationale is below.)

---

## What this dashboard is not

**Not [the daily glance](../daily-glance/daily-health.md).** The daily glance is the morning rail check — 30 seconds, action and health signals, close if green. Weekly review is the knowledge ritual — 90 minutes, deliberate human decisions about content. Different rhythm, different scope, different cognitive mode.

**Not one monolithic page.** The ritual uses the Inbox queue, Maintenance's Drift watch / Loose ends / New this week sections, and Knowledge's claim views. Weekly review is the order of operations, not a separate runtime dashboard.

**Not auto-actioned.** Every section requires a human decision: promote or defer, archive or keep, include or exclude. Nothing in this ritual changes state on its own. The human is the agent of all state changes it surfaces.

---

## Why it's designed this way

**Top-to-bottom ordering follows the workflow logic.** Inbox review unblocks downstream synthesis, so it comes first. Promotion comes before metrics because the metrics reflect promotion behavior — reviewing metrics before doing the promotions would show stale numbers. The sequence is not aesthetic; it is causal.

**Empty sections are the goal, not a bug.** A healthy week leaves most sections empty — recognizing that as success rather than a broken view is the cross-cutting [empty-is-success principle](../README.md#why-the-dashboards-are-designed-the-way-they-are), applied here per section.

**The orphan check has a coverage angle.** Beyond the raw orphan count (notes with zero inbound links), the check surfaces qualifying notes that should connect to current work but don't. This catches missing coverage, not just disconnected notes — the difference between a note that genuinely stands alone and a note that should be connected but hasn't been.

**Schema migration progress lives in Maintenance.** Structural maintenance (schema drift, plugin config changes) belongs in Drift watch. The weekly review includes that check, but does not turn structural drift into a content-decision queue.

---

## Related

**Explanation**

- The morning glance this complements: [Daily glance](../daily-glance/daily-health.md)
- Reading-side companion: [Reading pipeline](../synthesis-agenda/reading-pipeline.md)
- Why the ritual matters: [The knowledge cycle](../../knowledge/knowledge-cycle.md)
- The dashboards overview: [Dashboards](../README.md)

**How-to**

- How to run the ritual: [run the weekly review](../../../how-to-guides/inbox/run-the-weekly-review.md)

**Background**

- Structural drift companion: [Drift watch](drift-watch.md)
