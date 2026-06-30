---
title: Kanban board
parent: Explanation
nav_order: 5
has_children: true
permalink: /explanation/kanban-board/
---

# The Kanban board

The Kanban board is Memoria's **control plane** — the trigger-and-lanes end of the loop. Every unit of background **agent** work is a card on the Hermes board (`kanban.db`, projected into Obsidian): a human action (or cron) creates a card, the dispatcher assigns it to a **lane**, the lane's agent runs it, and the result resurfaces as an **Inbox** signal. It should feel like a teammate working in the background — invisible until it has something for you.

**Lanes are active board routes** — alpha.11 dispatches `catalog`, `extract`, `link`, and `map` to the Librarian, and `verify` to the Peer-reviewer. Writer/`draft` and Engineer/`code` profile packages ship deferred. The Co-PI has no lane (it converses in the pane and delegates), and neither do deterministic operations; see [Profiles](../profiles/README.md) and [Operations](../operations.md).

The board's central design move is to keep three dimensions separate — the hidden execution `status`, the PI-facing attention state, and a soft `agent_recommendation` — so "a worker finished" never silently becomes "a human approved." Why they stay separate, and why a rejected card spawns a fresh one rather than reopening, is developed in [Board states and the review gate](states.md); the enums and lane assignments are in the [Kanban board reference](../../reference/kanban-board.md). A card is *work* (transient, archived when done); a vault note is *knowledge* (durable).

## Documents in this section

| Page                                                          | What it covers                                                                                                                                                                          |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Board states and the review gate](states.md)                 | What a card carries; why execution, review, and PI-facing attention state are separate; and why rejection spawns a new card. |
| [The honesty card](honesty-card.md)                            | The card the PI actually reads: argument for, argument against, what tipped it, certainty — and no verdict on proposals; finding-first verification cards; graded loudness.               |
| [Decision points](decision-points.md)                         | Approval gates, work prompts, batch worklists, and automated steps. |
| [How the board surfaces in Obsidian](obsidian-projection.md)  | The read-only projections — the Inbox queue view and the `system/board/` worker-card export — that let Obsidian read the authoritative `kanban.db`.                    |
| [WIP limits and back-pressure](wip-limits.md)                 | Why lane concurrency and review caps intentionally slow work before review quality degrades. |

For the state lookup tables (enums, lane assignments, WIP caps, dispatch settings, and the post-rejection paths), see the [Kanban board reference](../../reference/kanban-board.md).

## Related

**Explanation**

- Why review is structural: [Why the review gate is structural](../../design/why-review-gate-is-structural.md)
- The decision model behind the cards: [Decision points](decision-points.md)
- The Inbox card types: [Document types and epistemic roles](../knowledge/document-types.md)

**Dashboards**

- The Inbox board view: [The board-state dashboard](../dashboards/daily-glance.md#board-state-support)
