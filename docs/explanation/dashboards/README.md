---
title: Dashboards
parent: Explanation
nav_order: 8
has_children: true
permalink: /explanation/dashboards/
---

# Dashboards

The **Inbox** is the *action queue* — discrete things that need you now. **Dashboards** are *browsable health views* — where things stand. They live in `spaces/`, `system/dashboards/`, and related Base files, are Bases/Dataview-backed and consumer-only, and a healthy vault shows them near-empty. Each answers one type of question; they are grouped by the kind of attention they demand:

| Group                                              | Dashboards                                                      | When you look                                     |
| -------------------------------------------------- | --------------------------------------------------------------- | ------------------------------------------------- |
| [Daily glance](daily-glance/README.md)             | Rail Now, Inbox queue action view                            | Start of every session — "what needs me?"         |
| [Synthesis agenda](synthesis-agenda/README.md)     | Reading pipeline, Discuss queue, Open questions, Contradictions | When deciding what to read, discuss, or reconcile |
| Project space                                      | Project gate                                                   | When steering a bounded inquiry to output          |
| [Structural health](structural-health/README.md)   | Maintenance collection, Drift watch, Loose ends, Board state  | Weekly maintenance and drift checks               |
| [Operational health](operational-health/README.md) | Fleet health, Audit log, Eval trend, Skill state            | When checking how the agent fleet is performing   |

The daily glance starts in the rail's **Now**: the Inbox is the daily action queue,
and Maintenance is the weekly structural-debt collection behind the health band.
**Board state is the Inbox board itself** — a Base over `inbox/`, not a separate query
page. Project gate is the Project space's steering surface: active thesis, saturation,
and structural-impact cache state. The synthesis-vs-structural split is by *actor*:
open-questions and contradictions are the **PI's** unfinished thinking; loose-ends and
drift-watch are the **Linter operation's** structural debt — kept separate, not collapsed.

## Why the dashboards are designed the way they are

Several principles cut across all of them.

Each dashboard surfaces one type of decision. Mixed queries produce lists the human can't batch-act on — a dashboard that asks "review these cards AND check these orphan notes" forces context-switching within a single glance. The single-decision constraint keeps the cognitive mode coherent.

The default state — nothing to review, everything healthy — should produce an empty or near-empty dashboard, not a list of green checks. Tables that always have rows train the human to ignore them. A dashboard that is always busy is a dashboard that stops being read. Empty is success, not a broken query.

Sort direction follows the decision type. Queues sort oldest-first because the oldest unreviewed item has waited the longest and should be acted on first. Logs sort newest-first because the most recent event is most actionable — investigating a log means starting from what just happened.

When a dependency is missing (a log file not yet created, fleet volume too low for meaningful statistics), dashboards show explanatory text rather than an error or a blank table. The graceful degradation is intentional: a new vault should not look broken just because data is still accumulating.

---

## Related

- Dashboard lookup table (source files, sort orders): [Dashboards](../../reference/dashboards.md)
- How to operate the dashboards: [Navigate the dashboards](../../how-to-guides/using-obsidian/navigate-the-dashboards.md)
- The primary weekly entry point: [Run the weekly review](../../how-to-guides/inbox/run-the-weekly-review.md)
