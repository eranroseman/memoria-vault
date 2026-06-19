---
title: Workflows
parent: Explanation
nav_order: 6
has_children: true
permalink: /explanation/workflows/
---

# The workflow model

Memoria's workflows are **state-machine paths on the board**, not scripted procedures: work lives as a card whose state is explicit, persistent, and queryable, so it survives across sessions and recovers from failure instead of breaking like a script. This section explains what coordinates work (the board), why the human owns every synthesis boundary (review as a state), and where automation is intended to step in.

## Documents in this section

| Page                                                                          | What it covers                                                                                                                                                       |
| ----------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [The board as a state machine (the control plane)](board-as-state-machine.md) | Why Kanban is the coordination layer (not chat), what a card carries, the card lifecycle, why cards and notes differ, and why there is no Orchestrator.              |
| [Review as a first-class state](review-as-state.md)                           | Why review is a structured field rather than a convention, what "blocking" means technically, and the post-rejection paths.                                          |
| [Verify-on-commit](verify-on-commit.md)                                       | How draft commits enqueue Peer-reviewer verification cards through the post-commit hook. |

For step-by-step workflow recipes, see [how-to guides](../../how-to-guides).
