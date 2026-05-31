
# The board-state dashboard

The board-state dashboard is the human's Obsidian window into the Hermes Kanban board: active cards, review queue, retry watch, and claim-note maturity histogram. Open it when you're already in Obsidian and want to see card state without switching to the Hermes workspace view.

---

## What this dashboard is not

**Not the authoritative board.** The authoritative board lives in Hermes (or in `00-meta/board/` as markdown cards, depending on configuration). Board-state is a *read view*. State changes happen through Hermes commands or by editing card files directly, not through this dashboard.

**Not [Daily Health](daily-health.md)'s "today's queue."** Daily Health shows only `blocked` cards and those awaiting review, capped at ten. Board-state shows the full board across all states — every active card, every lane, everything in retry watch.

**Not [discuss-queue](discuss-queue.md).** Discuss-queue is an upstream-cognitive-discipline view — paper notes classified but not yet Socratically processed. Board-state is a workflow-execution view — cards moving through states regardless of content type.

---

## Why it's designed this way

**Three sections, three distinct failure modes.** Active cards surface work-in-flight visibility. The review queue shows who owes what review — the human's obligation toward agent output. Retry watch shows which cards are accumulating retries — the signal that something is broken rather than just slow. Each section names a different thing that can go wrong; separating them prevents the human from having to parse a single mixed list.

**The claim-note maturity histogram is an end-of-board signal.** The board processes upstream work; claim notes at `maturity: seedling → budding → evergreen` are the downstream output of that work. A board that flows cards without producing maturity is a board that is not advancing the knowledge graph. Showing both on the same dashboard makes the throughput relationship visible.

**Markdown-backed only.** The dashboard queries assume board cards are represented as markdown files in `00-meta/board/`. If Hermes is the sole source of truth and there is no markdown export, this dashboard is intentionally empty — Hermes Workspace is the right surface in that case.

---

## Related

- Filtered daily subset: [Daily Health](daily-health.md)
- Upstream-discipline complement: [discuss-queue](discuss-queue.md)
- Recovery guides for board problems: [fix a stuck card](../../how-to-guides/recovery/fix-stuck-card.md)
- Kanban state machine explanation: `kanban-board/README.md`
