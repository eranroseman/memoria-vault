---
title: The board-state dashboard
parent: Daily glance
nav_order: 2
grand_parent: Dashboards
---

# The board-state dashboard

The board-state dashboard (`system/dashboards/board-state.md`) is the full Inbox board — the agent→human action queue. Open it when Home's "Needs me" view isn't enough and you want everything: every card, every state, plus what the workers are executing underneath.

---

## What it shows

The page is built on **`inbox.base`** — the one Obsidian Base over `inbox/`, grouped by card type ([ADR-51](../../../adr/51-inbox-category-and-honesty-card.md)). Its **"Needs me"** view (cards in `proposed` — the same view the Inbox space embeds) comes first; an **"All cards"** view (everything in flight, whatever its state) follows. A third section lists the **live worker cards** — the read-only markdown exports in `system/board/` that mirror what each Hermes lane is currently executing.

Cards in `proposed` are waiting on you; the queue converges to empty. That convergence is the design: batch screening never lands here as N cards (one aggregate work-prompt points at the worklist instead), so a long queue always means real decisions, not noise.

---

## What this dashboard is not

**Not a separate query page.** Board state *is* the Inbox rendered through a Base — the same files, the same state. Acting on a card here (its lifecycle edit) is the real action, not a mirror of one.

**Not the authoritative execution board.** The worker-card section reads the `system/board/` projections of `kanban.db`. Those are one-way and ephemeral — editing a projected file does nothing; the execution `status` chain is the hidden mechanic the PI never manages.

**Not Home's "Needs me" view.** Home shows only the `proposed` slice, capped for a 30-second glance. Board-state shows the whole board — everything in flight, plus the worker layer.

**Not [The discuss-queue dashboard](../synthesis-agenda/discuss-queue.md).** Discuss-queue is a Library-side cognitive-discipline view — sources read but not yet distilled. Board-state is the action-and-execution view — cards, regardless of content.

---

## Why it's designed this way

**One Base, several views — not several dashboards.** "What needs me?", "what's in flight?", and "what are the workers doing?" are slices of one queue. Keeping them as views of `inbox.base` means there is exactly one definition of a card and one place its state lives.

**The lifecycle chain is the card state you see.** No execution vocabulary leaks into the view: `proposed` = awaiting you, `current` = acted on, `archived` = closed — the same chain every note uses, scoped to `inbox/` so card-state and note-state never collide.

**Worker cards are included but last.** They answer "is the machine actually working?" — useful when a lane seems stuck — but they are the mechanic's view, deliberately below the decisions the PI owns.

---

## Related

- The launch surface this feeds: [The daily glance view](daily-health.md)
- How the projections work: [How the board surfaces in Obsidian](../../kanban-board/obsidian-projection.md)
- The card format: [The honesty card](../../kanban-board/card-schema.md)
- Troubleshooting board problems: [Fix a stuck card](../../../how-to-guides/troubleshooting/fix-stuck-card.md)
