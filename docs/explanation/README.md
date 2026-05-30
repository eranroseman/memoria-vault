---
topic: general
---

# Explanation

Understanding-oriented documents: what Memoria is, how it's structured, and *why* it's built that way. These are for reading and reflection, not for following step-by-step — for that, see [tutorials/](../tutorials/) and [how-to/](../how-to/); for exact values, see [reference/](../reference/).

## The conceptual map

Read from the inside out: what the system is, then how it's structured, then how each design area works.

1. **[vision.md](vision.md)** — purpose, design goals, what Memoria is and is not. Start here.
2. **[architecture/](architecture/)** — the three-layer model (board, workers, vault): the control plane, the review gate, memory tiers, distribution, and the *why* rationale docs.

Then the design areas, each a concept folder:

- **[dashboards/](dashboards/)** — the Dataview dashboards that surface what's overdue, stalled, or drifting.
- **[kanban-board/](kanban-board/)** — the control plane: states, the review gate, the card and handoff schema.
- **[profiles/](profiles/)** — the seven Hermes workers, their missions, lanes, and delegation rules.
- **[obsidian-ui/](obsidian-ui/)** — how the human interacts: workspaces, callouts, the home note, and UI discipline.
- **[obsidian-plugins/](obsidian-plugins/)** — why each plugin is in (or out of) the set, and config governance.
- **[workflows/pipeline-design.md](workflows/pipeline-design.md)** — why workflows are state-machine paths on the board, not scripted procedures.
- **[vault/](vault/)** — the durable knowledge store: folder taxonomy, the promotion map, and pitfalls.
- **[operations/](operations/)** — system mechanisms such as session logging.

## For decisions and direction

The *why* behind a specific choice usually lives in an ADR, and the forward plan lives in the roadmap — both are in [project/](../project/): [decisions/](../project/decisions/) for the ADRs, [roadmap/](../project/roadmap/) for direction.
