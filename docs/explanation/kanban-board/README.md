---
title: Kanban board
parent: Explanation
nav_order: 6
has_children: true
permalink: /explanation/kanban-board/
---


# The Kanban board

The Kanban board is Memoria's **control plane** — the shared state machine that tracks every piece of in-progress work across profiles and sessions. Every meaningful operation produces a card that lives on the board until a human approves it into the vault, fails it, or decides it shouldn't exist. Nothing becomes canonical without passing through the board.

The board's central design move is to keep a card's three dimensions separate — **execution** (`status`), **review** (`metadata.review_status`), and **agent recommendation** (`metadata.agent_recommendation`) — so that "a worker finished" never silently becomes "a human approved." A card is *work* (transient, board-resident, archived when done); a vault note is *knowledge* (durable). The pages below explain how that state machine is shaped, why the card schema is split, and how the board surfaces read-only in Obsidian.

## Documents in this section

| Page | What it covers |
| --- | --- |
| [Board states and the review gate](states.md) | Why execution and review are two separate lifecycles, what each transition means, the five rules of the review gate, where the WIP limits sit, and why Socratic is not a board lane. |
| [Why the card schema is split](card-schema.md) | Why a card is Hermes' fixed fields plus a Memoria `metadata` overlay, why `review_status` is separate from `status`, and why the handoff payload is self-contained. |
| [How the board surfaces in Obsidian](obsidian-projection.md) | The two one-way, ephemeral projections — the `99-system/board/` markdown export and the `board-state.jsonl` snapshot — that let Dataview and the status line read the authoritative `kanban.db`. |

For the state lookup tables (the `status` and `review_status` enums, lane assignments, WIP caps, dispatch settings, and the post-rejection paths), see the [Kanban board reference](../../reference/kanban-board.md).

## Related

**Explanation**

- State machine and the card lifecycle: [The board as a state machine (the control plane)](../workflows/board-as-state-machine.md)
- Why review is structural: [Why the review gate is structural](../rationale/why-human-gate.md)
- The board as control plane: [Why three layers, not one](../rationale/why-three-layers.md)
- Profiles that interact with the board: [Profiles](../profiles/README.md)
- Flows that run on the board: [Workflows](../workflows/README.md)

**Dashboards**

- The dashboard that reads the board export: [The board-state dashboard](../dashboards/daily-glance/board-state.md)
