---
title: How the board surfaces in Obsidian
parent: Kanban board
grand_parent: Explanation
nav_order: 3
---

# How the board surfaces in Obsidian

The authoritative board lives in `kanban.db` — a database Obsidian cannot query directly. The PI never opens it. What they see instead is the **Inbox**: the PI's slice of the board, rendered through Obsidian's own view layer.

---

## The Inbox board: `inbox.base`

The board the PI works is **one Obsidian Base over `inbox/`** — `inbox.base`, grouped by card type, filtered on the lifecycle chain. Its **"Needs me" view** (proposed `candidate`, `gap`, and `work-prompt` cards) is shown on the Inbox queue ([ADR-81](../../adr/81-persistent-gate-dashboards.md)); flags and alerts are read from Maintenance. The full board (every card, every state) is the same Base's wider view, surfaced as the [board-state dashboard](../dashboards/daily-glance/board-state.md). No plugin, no custom renderer: cards are markdown notes with frontmatter, and Bases is the vault's standard view layer.

This is why the board needs no bespoke UI — the Inbox category *is* agent→human messaging ([ADR-51](../../adr/51-inbox-category-and-honesty-card.md)), and a Base over it is automatically the kanban view, grouped by type, converging to empty.

## The worker-card export: `system/board/`

At the top of the Inbox sits the execution layer. QuickAdd and Co-PI delegation seed a disposable `system/board/` projection as soon as a task is created, and board export then reconciles each live Hermes worker card from `kanban.db` on a ~60-second cadence (matching the dispatcher's tick, so the projection never lags the board by more than one cycle). Each file carries the queryable fields in frontmatter plus the handoff summary in the body. The Inbox embeds a compact Activity view over these files only while a task is `triage`, `todo`, `ready`, or `running`; done and blocked tasks leave Activity and surface through result prompts, blocker tickets, or Maintenance.

The same pass appends a compact snapshot line to `system/logs/board-state.jsonl` with per-lane counts and review-queue depth. The snapshot feeds telemetry and diagnostics; the PI-facing surfaces stay on native Inbox and board Bases.

## The two layers meet at terminal states

The layers are not parallel feeds the PI has to watch separately: in-process task status stays in Activity, and only human work enters **Needs me**. When the export pass observes a worker card transition into `done` with `review_status: requested`, it raises **one `work-prompt` card in the Inbox** — the verdict-free "a lane finished, here's where to look" shape owned by [The honesty card](card-schema.md). When a card blocks, export raises one domain-specific ticket where possible, or a generic blocked `work-prompt` as fallback. The emits are idempotent — the export diffs against its state cache and names each prompt after the card id, so a review request or blocker raises exactly one prompt.

---

## The projections are one-way and ephemeral

Editing a projected file in `system/board/` does nothing to the board — the export is regenerated each pass and any manual edit is overwritten. The split of authority is deliberate: **Inbox cards are real notes** (acting on one — `proposed` → `current` — is a real state change the PI makes), while **worker-card exports are read views** of Hermes state, which changes only through Hermes itself.

---

## Related

- Conceptual overview: [Kanban board](README.md)
- The dashboard built on `inbox.base`: [The board-state dashboard](../dashboards/daily-glance/board-state.md)
- Export file schemas (`board-state.jsonl`, frontmatter fields): [Telemetry log schemas](../../reference/telemetry-logs.md)
- The separate fleet-health metrics roll-up: [fleet-health dashboard](../dashboards/operational-health/fleet-health.md)
