---
topic: board
---

# Board export and aggregation

> **Status: Phase 1 (ships with v0.1).** The board is the Hermes-native Kanban (`~/.hermes/kanban.db`). The **board export** described below is implemented in `.memoria/mcp/board_export.py` (shipped — writes the `00-meta/board/` markdown projection and the `board-state.jsonl` snapshot from `hermes kanban list --json`). The **metrics aggregator** (`00-meta/08-metrics/`) is still pending. The earlier "Phase 4" tag was a misclassification. See [implementation-status.md](../../project/implementation-status.md).

The authoritative board lives in the Hermes built-in Kanban (`kanban.db`). Two read-only projections make it visible to Obsidian's Dataview-based surfaces, since Dataview cannot query the database directly.

## Board export → `00-meta/board/`

A scheduled exporter projects each live card to a markdown file under `00-meta/board/` so the [board-state dashboard](../dashboards/board-state.md) can query them with Dataview. Per card it denormalizes the queryable fields: `task_id`, `status`, `assignee`, `review_status`, `retry_count`, `reason`, `last_updated`, and the handoff summary. The export is one-way (db → markdown); editing the markdown does not change the board.

## Board-state snapshot → `board-state.jsonl`

For the [status line](../../reference/obsidian-ui/status-line.md) (a glanceable widget that needs counts, not full cards), the dispatcher also writes a compact `board-state.jsonl` snapshot — one line per refresh with per-lane counts (`running`, `ready`, `blocked`, `review-queue depth`). The status-line wrapper polls the Hermes API (port 8642) and reads this snapshot rather than re-querying the database.

## Metrics aggregation → `00-meta/08-metrics/`

A scheduled aggregator rolls run history into `lane-metric` / `skill-metric` notes under `00-meta/08-metrics/` (also deferred — not yet built), which the [fleet-health dashboard](../dashboards/fleet-health.md) reads for the trust score. The aggregator is required by Memoria v0.1 but not yet implemented; it activates meaningfully once the fleet has accumulated real weekly volume.

## Ownership

The **dispatcher** owns the snapshot and the markdown export (state transitions it already performs). The **Linter** owns rotation/cleanup of the projected files (its `authorized-targeted` class). No agent edits the projections as content.

## Related

- [card-schema.md](card-schema.md) — the card fields these projections denormalize.
- [dashboards/board-state.md](../dashboards/board-state.md), [dashboards/fleet-health.md](../dashboards/fleet-health.md), [obsidian-ui/status-line.md](../../reference/obsidian-ui/status-line.md) — the consumers.
