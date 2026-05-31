# Dashboards

Memoria ships ten dashboards in `00-meta/01-dashboards/`. Each answers one type of question about the vault. They are grouped here by the kind of attention they demand.

## Daily glance

| Dashboard | Question it answers |
| --- | --- |
| [daily-health.md](daily-health.md) | Is anything broken right now? What needs attention today? |
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

## Design rules that apply to all dashboards

- **One decision per query.** Each dashboard query surfaces one type of thing the human needs to act on. Mixed queries produce lists the human can't batch-act on.
- **Filter the boring cases.** The default state — nothing to review, everything healthy — should show nothing, not a list of green checks. Dataview tables that always have rows train the human to ignore them.
- **Sort oldest-first for queues, newest-first for logs.** Oldest-unreviewed items get priority; most-recent events are most actionable in logs.
- **Graceful degradation.** When a dependency is missing (a plugin not installed, a log file not yet created), the dashboard shows explanatory text rather than an error or an empty table.
