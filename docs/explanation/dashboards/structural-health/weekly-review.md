---
title: The weekly-review dashboard
parent: Structural health
nav_order: 3
grand_parent: Dashboards
---


# The weekly-review dashboard

The weekly-review dashboard is the Friday-ritual entry point. It gathers the week's accumulated content decisions — a full Inbox, candidate cards awaiting triage, claim maturity to revisit, orphans, project pages, the quiet-level findings — into one ordered surface so the ritual has a single starting place rather than six. The discipline is **one ritual per week, ~90 minutes** — not "open whenever." A weekly cadence is what prevents the vault from accumulating drift faster than it produces synthesis. (For the actionable top-to-bottom sequence, see [run the weekly review](../../../how-to-guides/curate/run-the-weekly-review.md); the ordering rationale is below.)

---

## What this dashboard is not

**Not [Daily Health](../daily-glance/daily-health.md).** The daily glance (absorbed into the Inbox launch surface) is the morning health check — 30 seconds, system signals, close if green. Weekly review is the knowledge ritual — 90 minutes, deliberate human decisions about content. Different rhythm, different scope, different cognitive mode.

**Not the only weekly view.** The `reading-pipeline`, `loose-ends`, and `drift-watch` dashboards are also recommended-weekly — but weekly-review is the ritual *entry point* that links to them and defines the order. It is the orchestrator of the weekly ritual, not just one surface among several.

**Not auto-actioned.** Every section requires a human decision: promote or defer, archive or keep, include or exclude. Nothing in this dashboard is triggered by a cron job. The human is the agent of all state changes it surfaces.

---

## Why it's designed this way

**Top-to-bottom ordering follows the workflow logic.** Inbox review unblocks downstream synthesis, so it comes first. Promotion comes before metrics because the metrics reflect promotion behavior — reviewing metrics before doing the promotions would show stale numbers. The sequence is not aesthetic; it is causal.

**Empty sections are the goal, not a bug.** A healthy week leaves most sections empty — recognizing that as success rather than a broken dashboard is the cross-cutting [empty-is-success principle](../README.md#why-the-dashboards-are-designed-the-way-they-are), applied here per section.

**The orphan check has a coverage angle.** Beyond the raw orphan count (notes with zero inbound links), the check surfaces qualifying notes that should connect to current work but don't. This catches missing coverage, not just disconnected notes — the difference between a note that genuinely stands alone and a note that should be connected but hasn't been.

**Schema migration progress lives elsewhere.** Structural maintenance (schema drift, plugin config changes) belongs in `drift-watch`, not here. Weekly-review surfaces content decisions; mixing structural maintenance into the same ritual crowds the human's Friday attention with two different cognitive tasks.

---

## Related

**Explanation**

- The morning glance this complements: [Daily Health](../daily-glance/daily-health.md)
- Reading-side companion: [The reading-pipeline dashboard](../synthesis-agenda/reading-pipeline.md)
- Why the ritual matters: [The knowledge cycle](../../knowledge/knowledge-cycle.md)
- The dashboards overview: [Dashboards](../README.md)

**How-to**

- How to run the ritual: [run the weekly review](../../../how-to-guides/curate/run-the-weekly-review.md)

**Background**

- Structural drift companion: `drift-watch`
