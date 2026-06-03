---
title: How the board surfaces in Obsidian
parent: Kanban board
nav_order: 3
---


# How the board surfaces in Obsidian

The authoritative board lives in `kanban.db` — a database Dataview cannot query directly. Two read-only projections bridge the gap so the human can see board state from inside Obsidian.

---

## The two projections

**Board export → `99-system/board/`** — a `board_export.py` job writes each live card to a markdown file on a **~60-second cadence** (matching the dispatcher's tick, so the projection never lags the board by more than one cycle). The [board-state dashboard](../dashboards/daily-glance/board-state.md) reads these files via Dataview. Each file carries the queryable fields in frontmatter (`task_id`, `status`, `assignee`, `review_status`, `retry_count`) plus the human-readable handoff summary in the body.

**Board-state snapshot → `board-state.jsonl`** — the same ~60s pass appends a compact JSONL line with per-lane running/ready/blocked counts and review-queue depth. The [status-line widget](../obsidian/the-status-line.md) reads this instead of re-querying the database, keeping its refresh lightweight.

---

## The projections are one-way and ephemeral

Editing a projected markdown file does nothing to the board. The projections are regenerated on each pass; any manual edit is overwritten. The board stays authoritative; the markdown is a read view.

---

## Related

- Conceptual overview: [Kanban board](README.md)
- The dashboard that reads the board export: [The board-state dashboard](../dashboards/daily-glance/board-state.md)
- The status line that reads the snapshot: [The status line](../obsidian/the-status-line.md)
- Export file schemas (`board-state.jsonl`, frontmatter fields): [Telemetry reference](../../reference/telemetry.md)
- The separate fleet-health metrics roll-up: [fleet-health dashboard](../dashboards/operational-health/fleet-health.md)
