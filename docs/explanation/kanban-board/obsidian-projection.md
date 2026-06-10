---
title: How the board surfaces in Obsidian
parent: Kanban board
nav_order: 3
---

# How the board surfaces in Obsidian

The authoritative board lives in `kanban.db` — a database Obsidian cannot query directly. The PI never opens it. What they see instead is the **Inbox**: the PI's slice of the board, rendered through Obsidian's own view layer.

---

## The Inbox board: `inbox.base`

The board the PI works is **one Obsidian Base over `inbox/`** — `inbox.base`, grouped by card type, filtered on the lifecycle chain. Its **"Needs me" view** (cards in `proposed`) is embedded above the fold in `home.md`, so the front door *is* the action queue; the full board (every card, every state) is the same Base's wider view, surfaced as the [board-state dashboard](../dashboards/daily-glance/board-state.md). No plugin, no custom renderer: cards are markdown notes with frontmatter, and Bases is the vault's standard view layer.

This is why the board needs no bespoke UI — the Inbox category *is* agent→human messaging ([ADR-51](../../adr/51-inbox-category-and-honesty-card.md)), and a Base over it is automatically the kanban view, grouped by type, converging to empty.

## The worker-card export: `system/board/`

Below the Inbox sits the execution layer. A board-export cron projects each live Hermes worker card from `kanban.db` to a markdown file in `system/board/` on a ~60-second cadence (matching the dispatcher's tick, so the projection never lags the board by more than one cycle). Each file carries the queryable fields in frontmatter plus the handoff summary in the body. This is the *mechanic's view* — useful when you want to see what a lane is actually executing — not part of the daily surface.

The same pass appends a compact snapshot line to `system/logs/board-state.jsonl` with per-lane counts and review-queue depth; Home's status glance and the [status line](../obsidian/the-status-line.md) read this instead of re-querying the database, keeping their refresh lightweight.

---

## The projections are one-way and ephemeral

Editing a projected file in `system/board/` does nothing to the board — the export is regenerated each pass and any manual edit is overwritten. The split of authority is deliberate: **Inbox cards are real notes** (acting on one — `proposed` → `current` — is a real state change the PI makes), while **worker-card exports are read views** of Hermes state, which changes only through Hermes itself.

---

## Related

- Conceptual overview: [Kanban board](README.md)
- The dashboard built on `inbox.base`: [The board-state dashboard](../dashboards/daily-glance/board-state.md)
- The status line that reads the snapshot: [The status line](../obsidian/the-status-line.md)
- Export file schemas (`board-state.jsonl`, frontmatter fields): [Telemetry & logs](../../reference/telemetry.md)
- The separate fleet-health metrics roll-up: [fleet-health dashboard](../dashboards/operational-health/fleet-health.md)
