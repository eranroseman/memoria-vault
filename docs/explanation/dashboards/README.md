# Dashboards

Memoria ships ten dashboards in `00-meta/01-dashboards/`. Each answers one type of question about the vault. They are grouped here by the kind of attention they demand. (The Daily Health view is implemented as the dashboards' `index.md` home page — there is no separate `daily-health.md` file in the vault.)

## Daily glance

| Dashboard | Question it answers |
| --- | --- |
| [daily-health.md](daily-health.md) | Is anything broken right now? What needs attention today? (implemented as `index.md`) |
| [board-state.md](board-state.md) | What work is in flight? Where are cards stuck? |

## Synthesis agenda

| Dashboard | Question it answers |
| --- | --- |
| [reading-pipeline.md](reading-pipeline.md) | What's queued, classified, and ready for claim-note writing? |
| [discuss-queue.md](discuss-queue.md) | Which paper notes are waiting for a Socratic discussion pass? |
| [open-questions.md](open-questions.md) | What open questions has past synthesis raised? |
| [contradictions.md](contradictions.md) | Which claim notes disagree with each other? |

## Structural health

| Dashboard | Question it answers |
| --- | --- |
| [drift-watch.md](drift-watch.md) | What structural drift has the Linter detected? |
| [loose-ends.md](loose-ends.md) | Which files are named `TODO`, `tmp`, or `untitled`? |
| [weekly-review.md](weekly-review.md) | What needs attention this week across all categories? |

## Operational health

| Dashboard | Question it answers |
| --- | --- |
| [fleet-health.md](fleet-health.md) | Are the agents performing well over time? Is cost trending up? |
| [audit-log.md](audit-log.md) | What did the policy MCP allow, deny, and flag today? |

## Why the dashboards are designed the way they are

Several principles cut across all ten dashboards.

Each dashboard surfaces one type of decision. Mixed queries produce lists the human can't batch-act on — a dashboard that asks "review these cards AND check these orphan notes" forces context-switching within a single glance. The single-decision constraint keeps the cognitive mode coherent.

The default state — nothing to review, everything healthy — should produce an empty or near-empty dashboard, not a list of green checks. Dataview tables that always have rows train the human to ignore them. A dashboard that is always busy is a dashboard that stops being read. Empty is success, not a broken query.

Sort direction follows the decision type. Queues sort oldest-first because the oldest unreviewed item has waited the longest and should be acted on first. Logs sort newest-first because the most recent event is most actionable — investigating a log means starting from what just happened.

When a dependency is missing (a plugin not installed, a log file not yet created, fleet volume too low for meaningful statistics), dashboards show explanatory text rather than an error or a blank table. The graceful degradation is intentional: a new vault should not look broken just because data is still accumulating.
