---
title: Workflows
parent: Explanation
nav_order: 7
has_children: true
permalink: /explanation/workflows/
---

# The workflow model

Memoria's workflows are **state-machine paths on the board**, not scripted procedures: work lives as a card whose state is explicit, persistent, and queryable, so it survives across sessions and recovers from failure instead of breaking like a script. This section explains what flows through the system (two pipelines), what coordinates it (the board), why the human owns every synthesis boundary (review as a state), and where automation steps in (verify-on-commit).

Two pipelines run on the board: an **upstream** pipeline that brings new knowledge into the vault and a **downstream** pipeline that turns accumulated knowledge into deliverables. They run continuously and per-project respectively, not as one end-to-end script — see [The two pipelines](the-two-pipelines.md).

## Documents in this section

| Page | What it covers |
| --- | --- |
| [The two pipelines](the-two-pipelines.md) | The upstream (find → distill) and downstream (assess → export) pipelines, what each stage means, and why they run continuously rather than as one sequential script. |
| [The board as a state machine (the control plane)](board-as-state-machine.md) | Why Kanban is the coordination layer (not chat), what a card carries, the card lifecycle, why cards and notes differ, and why there is no Orchestrator. |
| [Review as a first-class state](review-as-state.md) | Why review is a structured field rather than a convention, what "blocking" means technically, and the post-rejection paths. |
| [Verify-on-commit](verify-on-commit.md) | Why committing a draft auto-creates a verification card, why the trigger is a git hook rather than a cron job, and why automatic creation is not automatic approval. |

For step-by-step workflow recipes, see [how-to guides](../../how-to-guides/).
