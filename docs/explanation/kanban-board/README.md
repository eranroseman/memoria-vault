---
title: Kanban board
parent: Explanation
nav_order: 5
has_children: true
permalink: /explanation/kanban-board/
---

# The Kanban board

The Kanban board is Memoria's **control plane** — the trigger-and-lanes end of the loop. Every unit of background **agent** work is a card on the Hermes board (`kanban.db`, projected into Obsidian): a human action (or cron) creates a card, the dispatcher assigns it to a **lane**, the lane's agent runs it, and the result resurfaces as an **Inbox** signal. It should feel like a teammate working in the background — invisible until it has something for you.

**Lanes are the four background agents** — Librarian, Writer, Peer-reviewer, Engineer (`assignee = memoria-<name>`). The Co-PI has no lane (it converses in the pane and delegates), and neither do the deterministic operations (ingest, search, clustering, sweeps, the Linter run on cron/CI) — why both stay off the board is in [Board states and the review gate](states.md).

The board's central design move is to keep three dimensions separate — the hidden execution `status`, the PI-facing lifecycle state, and a soft `agent_recommendation` — so "a worker finished" never silently becomes "a human approved." Why they stay separate, and why a rejected card spawns a fresh one rather than reopening, is developed in [Board states and the review gate](states.md); the enums and lane assignments are in the [Kanban board reference](../../reference/kanban-board.md). A card is *work* (transient, archived when done); a vault note is *knowledge* (durable).

## Documents in this section

| Page                                                          | What it covers                                                                                                                                                                          |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Board states and the review gate](states.md)                 | Why execution and the PI-facing lifecycle are two separate dimensions, what each transition means, why rejection spawns a new card, where the WIP limits sit, and why the Co-PI and the operations have no lanes. |
| [The honesty card](card-schema.md)                            | The card the PI actually reads: argument for, argument against, what tipped it, certainty — and no verdict on proposals; finding-first verification cards; graded loudness.               |
| [How the board surfaces in Obsidian](obsidian-projection.md)  | The read-only projections — the `inbox.base` board embedded in Home and the `system/board/` worker-card export — that let Obsidian read the authoritative `kanban.db`.                    |

For the state lookup tables (enums, lane assignments, WIP caps, dispatch settings, and the post-rejection paths), see the [Kanban board reference](../../reference/kanban-board.md).

## Related

**Explanation**

- Why review is structural: [Why the review gate is structural](../../design/why-human-gate.md)
- The decision model behind the cards: [Why promotion is gated](../knowledge/promotion-model.md)
- The Inbox card types: [Document types and epistemic roles](../knowledge/document-types.md)

**Dashboards**

- The Inbox board view: [The board-state dashboard](../dashboards/daily-glance/board-state.md)
