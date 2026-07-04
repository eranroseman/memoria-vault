---
title: Surfaces and dashboards
parent: Explanation
nav_order: 7
has_children: true
permalink: /explanation/dashboards/
---

# Surfaces and dashboards

The **Inbox** is the *action queue* — discrete things that need you now. **Dashboards** are *browsable health views* — where things stand. They live in `spaces/`, `system/dashboards/`, and related Base files, are Bases/Dataview-backed and consumer-only, and a healthy vault shows them near-empty. Each answers one type of question; they are grouped by the kind of attention they demand:

| Group                                              | Dashboards                                                      | When you look                                     |
| -------------------------------------------------- | --------------------------------------------------------------- | ------------------------------------------------- |
| [Daily glance](daily-glance.md)                    | Rail Now, Inbox queue action view                            | Start of every session — "what needs me?"         |
| [Synthesis agenda](synthesis-agenda.md)            | Reading pipeline, Discuss queue, Open questions, Contradictions | When deciding what to read, discuss, or reconcile |
| [Structural health](structural-health.md)          | Maintenance collection, Drift watch, Loose ends, Board state  | Weekly maintenance and drift checks               |
| [Operational health](operational-health.md)        | Audit log, Eval trend                                      | When checking runtime decisions and eval trends   |

The daily glance starts in the rail's **Now**: the Inbox is the daily action queue,
and Maintenance is the weekly structural-debt collection behind the health band.
**Board state is the standalone worker-debug dashboard**
(`system/dashboards/board-state.md`) — request and attention state for the local
worker, surfaced via the `memoria` request/attention commands — that the Inbox
links to, not the Inbox action queue itself. The Project space's gate is its own steering surface, not part of the dashboard
collection. The synthesis-vs-structural split is by *actor*:
open-questions and contradictions are the **PI's** unfinished thinking; loose-ends and
drift-watch are the **Linter operation's** structural debt — kept separate, not collapsed.

The exact shipped views, sources, and sort orders are in
[Dashboards](../../reference/dashboards.md).

---

## Related

- How to operate the dashboards: [Navigate Memoria surfaces](../../how-to-guides/using-obsidian/navigate-memoria-surfaces.md)
- The primary weekly entry point: [Run the weekly review](../../how-to-guides/inbox/run-the-weekly-review.md)
