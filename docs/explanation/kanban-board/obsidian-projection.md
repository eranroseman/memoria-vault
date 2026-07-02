---
title: How the board surfaces in Obsidian
parent: Kanban board
grand_parent: Explanation
nav_order: 4
---

# How the board surfaces in Obsidian

The authoritative board lives in `kanban.db` — a database Obsidian cannot query directly. The PI never opens it. What they see instead is the **Inbox**: the PI's slice of the board, rendered through Obsidian's own view layer.

---

## The Inbox board: `inbox.base`

The board the PI works is **one Obsidian Base over attention projections** — grouped by attention kind and filtered to what needs action. Its **"Needs me" view** is shown on the Queue ([ADR-116](../../adr/116-obsidian-surface-architecture.md)); flags and alerts are read from Maintenance. The full board is surfaced as the [board-state dashboard](../dashboards/daily-glance.md#board-state-support). No plugin, no custom renderer: projections are markdown notes with frontmatter, and Bases is the vault's standard view layer.

This is why the board needs no bespoke UI — the Inbox projection is agent-to-human messaging ([ADR-54](../../adr/54-two-decision-kinds-batch-worklists.md)), and a Base over it is automatically the kanban view, grouped by attention kind, converging to empty.

## The worker-card export: `system/board/`

At the top of the Inbox sits the execution layer. QuickAdd and Co-PI delegation seed a disposable `system/board/` projection as soon as a task is created; board export later reconciles it from Hermes. The Inbox embeds these files only while a task is `triage`, `todo`, `ready`, or `running`. Done and blocked tasks leave Activity and surface through result prompts, blocker tickets, or Maintenance.

Exact cadence, fields, logs, and cache behavior are reference material in [Board export](../../reference/board-export.md).

## The two layers meet at terminal states

The layers are not parallel feeds the PI has to watch separately: in-process status stays in Activity, and only human work enters **Needs me**. A `done` card with `review_status: requested` raises one review `work-prompt`; a blocked card raises one domain-specific ticket where possible, or a generic blocked prompt as fallback. Export is idempotent, so each review request or blocker raises once.

---

## The projections are one-way and ephemeral

Editing a projected file in `system/board/` does nothing to the board — the export is regenerated each pass and any manual edit is overwritten. The split of authority is deliberate: **Inbox cards are real notes** (acting on one — `proposed` → `current` — is a real state change the PI makes), while **worker-card exports are read views** of Hermes state, which changes only through Hermes itself.

---

## Related

- Conceptual overview: [Kanban board](README.md)
- The dashboard built on `inbox.base`: [The board-state dashboard](../dashboards/daily-glance.md#board-state-support)
- Export file schemas (`board-state.jsonl`, frontmatter fields): [Telemetry log schemas](../../reference/telemetry-logs.md)
