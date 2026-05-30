---
topic: dashboards
---

# `board-state` — design summary

**Runtime artifact.** Ships at `00-meta/01-dashboards/board-state.md` in the [starter vault](https://github.com/eranroseman/memoria-vault) and runs in Obsidian via Dataview; the runtime queries live there. This page covers the design role.

## Mission

A Dataview view of cards on the Hermes Kanban board: active cards, review queue, retry watch, claim-note maturity histogram. The board is the system's control plane; this dashboard is the human's window into it from inside Obsidian. Open when the Hermes Workspace board view isn't convenient — most often, when the human is already in Obsidian working with notes and wants to see card state without context-switching.

## What this dashboard is not

- **Not the authoritative board.** The authoritative board lives in Hermes (or in `00-meta/board/` as markdown cards, depending on configuration). This dashboard is a *read view*; state changes happen through Hermes commands or by editing the card files directly, not from inside this dashboard.
- **Not [Daily Health](daily-health.md)'s "today's queue" section.** Daily Health filters to `blocked` cards and those awaiting review (`review_status: requested`) only, capped at 10. `board-state` shows the full board across all states.
- **Not [`discuss-queue`](discuss-queue.md).** Discuss-queue is upstream-cognitive-discipline (paper notes classified but not Socratically processed); board-state is workflow-execution (cards moving through states regardless of content type).

## Design decisions

- **Markdown-backed only.** The queries assume the board is markdown-backed (cards as notes in `00-meta/board/`) or exported to markdown. If Hermes is the sole source of truth and there's no markdown export, this dashboard is empty by design — Hermes Workspace is the right surface in that case.
- **Three sections, three failure modes.** Active cards (work-in-flight visibility), review queue (who owes what review), retry watch (which cards are accumulating retries). Each one names a distinct human concern.
- **The claim-note maturity histogram is an end-of-board signal.** It tracks the downstream output of all the upstream board work — how many claim notes have advanced from `seedling` to `budding` to `evergreen`. A board that flows work without producing maturity is a board not advancing the knowledge graph.

## Related

- [kanban-board/README.md](../kanban-board/README.md) — Kanban state machine, lane definitions, review gate
- [glossary.md](../../reference/glossary.md#board-and-cards) — disambiguates the overloaded "review": `review_status`, `verdict`, and the Linter's verdict band
- [vault/README.md](../vault/README.md) — claim-note `maturity` stages (seedling → budding → evergreen) shown in the histogram
- [`discuss-queue`](discuss-queue.md) — upstream-discipline view (paper notes awaiting Socratic processing)
- [Daily Health](daily-health.md) — daily health glance, includes today's queue (filtered subset of board-state)
- [`audit-log`](audit-log.md) — per-decision forensics complementing board-level state
