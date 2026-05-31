
# Board export and aggregation

> **Status: deferred (Phase 4).** The export pipeline and metrics aggregator described here do not exist in the starter vault yet. This documents the intended design that the board-state dashboard, fleet-health dashboard, and status-line reference.

The authoritative board lives in the Hermes built-in Kanban (`kanban.db`). Obsidian's Dataview queries cannot reach that database directly — Dataview reads markdown files. The export pipeline bridges the gap with two read-only projections.

---

## Why projections rather than direct access

The separation between the authoritative board (Hermes) and the visible dashboards (Obsidian/Dataview) is intentional, not a technical limitation to work around.

**The board stays authoritative.** Card state changes happen through Hermes commands (`hermes kanban`), not by editing markdown. Dashboards are read views; they can never accidentally modify board state.

**Dataview queries stay simple.** Markdown files with frontmatter are what Dataview was designed to query. A projection that denormalizes the fields Dataview needs (status, assignee, review_status, retry_count) produces faster, simpler queries than any Dataview-to-SQLite bridge would.

**The projection is one-way and ephemeral.** Editing a projected markdown file does nothing to the board. The projection is regenerated on each export pass; any manual edits are overwritten. This makes the projection's role unambiguous.

---

## The two projections

**Board export → `00-meta/board/`**

The dispatcher periodically exports each live card to a markdown file under `00-meta/board/`. Each file carries the queryable fields in frontmatter: `task_id`, `status`, `assignee`, `review_status`, `retry_count`, `reason`, `last_updated`, plus the human-readable handoff summary in the body. The [board-state dashboard](../dashboards/board-state.md) reads these files.

**Board-state snapshot → `board-state.jsonl`**

For the status-line widget — which needs per-lane card counts, not full card content — the dispatcher also writes a compact JSON-lines snapshot. One line per refresh cycle, with running/ready/blocked counts per lane and the current review-queue depth. The status-line reads this snapshot rather than re-querying the database, keeping its refresh lightweight.

---

## Metrics aggregation

A scheduled aggregator rolls run history into `lane-metric` and `skill-metric` notes under `00-meta/08-metrics/`. These feed the fleet-health dashboard's trust score.

The aggregator activates meaningfully only once the system has accumulated real weekly volume — a fleet with two runs per week produces metrics that are statistically meaningless. Until volume is sufficient, the fleet-health dashboard degrades gracefully: the trust-score section states that data is accumulating rather than displaying misleading small-sample numbers.

---

## Ownership

The **dispatcher** owns both the markdown export and the board-state snapshot — it is already making the state transitions these projections reflect. The **Linter** owns rotation and cleanup of the projected files under its `authorized-targeted` auto-fix class. No agent edits the projections as content.

---

## Related

- The dashboard that reads the board export: [dashboards/board-state](../dashboards/board-state.md)
- The dashboard that reads the metrics aggregation: `dashboards/fleet-health`
- Card fields the projection denormalizes: [card-schema.md](card-schema.md)
