---
title: Dashboards
parent: Explanation
nav_order: 9
has_children: true
permalink: /explanation/dashboards/
---

# Dashboards

Memoria ships ten dashboards in `00-meta/01-dashboards/`. Each answers one type of question about the vault. They are grouped by the kind of attention they demand — four groups, each with its own page. (The Daily Health view is implemented as the dashboards' `index.md` home page — there is no separate `daily-health.md` file in the vault.)

| Group | Dashboards | When you look |
|---|---|---|
| [Daily glance](daily-glance/README.md) | Daily Health, Board state | Start of every session — "is anything wrong?" |
| [Synthesis agenda](synthesis-agenda/README.md) | Reading pipeline, Discuss queue, Open questions, Contradictions | When deciding what to read, discuss, or reconcile |
| [Structural health](structural-health/README.md) | Drift watch, Loose ends, Weekly review | Maintenance — the Friday ritual and drift checks |
| [Operational health](operational-health/README.md) | Fleet health, Audit log | When checking how the agent fleet is performing |

## Why the dashboards are designed the way they are

Several principles cut across all ten dashboards.

Each dashboard surfaces one type of decision. Mixed queries produce lists the human can't batch-act on — a dashboard that asks "review these cards AND check these orphan notes" forces context-switching within a single glance. The single-decision constraint keeps the cognitive mode coherent.

The default state — nothing to review, everything healthy — should produce an empty or near-empty dashboard, not a list of green checks. Dataview tables that always have rows train the human to ignore them. A dashboard that is always busy is a dashboard that stops being read. Empty is success, not a broken query.

Sort direction follows the decision type. Queues sort oldest-first because the oldest unreviewed item has waited the longest and should be acted on first. Logs sort newest-first because the most recent event is most actionable — investigating a log means starting from what just happened.

When a dependency is missing (a plugin not installed, a log file not yet created, fleet volume too low for meaningful statistics), dashboards show explanatory text rather than an error or a blank table. The graceful degradation is intentional: a new vault should not look broken just because data is still accumulating.

---

## Related

- How to operate the dashboards: [navigate-the-dashboards.md](../../how-to-guides/using-obsidian/navigate-the-dashboards.md)
- The primary weekly entry point: [run-the-weekly-review.md](../../how-to-guides/maintenance/run-the-weekly-review.md)
