---
topic: obsidian-ui
---

# Status line — the ambient indicator

Memoria's **status line** is a single glanceable indicator — two producers sharing one line, separated by a `·`. It is rendered as a **Dataview widget pinned in a note** (e.g., `00-meta/index.md`), *not* the Obsidian/OS status bar, which Dataview cannot write to; the effect is the same peripheral, always-in-view indicator (a true status-bar item would require a small custom plugin — deliberately avoided, see **Why no custom plugin** below):

## 1. Linter findings (lightweight)

The Linter's lightweight findings appear here, not in a callout or dashboard — a one-line "✓ Schema valid · ⚠ 2 broken links · ⚠ Note >800 words" that lets the human act on or dismiss issues without opening a separate report. Heavy lint findings (schema migrations, structural drift) escalate to a dashboard (the [`audit-log` dashboard](../../explanation/dashboards/audit-log.md) or the [`drift-watch` dashboard](../../explanation/dashboards/drift-watch.md)).

## 2. Kanban queue counts

A four-number summary of the board, also rendered as a one-liner:

```text
Active: 3 · Waiting: 2 · Review: 7 · Retries: 0
```

- **Active** — cards in `running` state across all lanes
- **Waiting** — cards in `blocked`
- **Review** — `done` cards awaiting review (`review_status: requested`)
- **Retries** — cards re-dispatched after a recoverable failure (back in `ready`)

Click anywhere in the four counts → opens [`board-state.md`](../../explanation/dashboards/board-state.md). The indicator is glanceable; the drill-down lives in the dashboard.

**Implementation.** A Dataview inline query in the human's daily note (or a pinned `00-meta/index.md`-resident widget), not a custom plugin. The Dataview query reads the Hermes Kanban state — either from a periodically-refreshed `board-state.jsonl` snapshot the dispatcher writes, or via a small wrapper that polls the Hermes API on port 8642. Memoria doesn't ship a standard implementation here; human setups vary too much.

**Why no custom plugin.** A 20-line plugin to render the same numbers would add maintenance overhead for a feature Dataview can deliver. The plugin would also have to handle authentication to the Hermes API; the Dataview approach reads a vault file the dispatcher already writes for the [`board-state` dashboard](../../explanation/dashboards/board-state.md).

## Composite line shape

The two producers co-exist on one line, Linter first then Kanban:

```text
✓ Schema valid · 2 broken links · Active: 3 · Waiting: 2 · Review: 7 · Retries: 0
```

When everything is quiet, the line is reassuringly short:

```text
✓ · 0 · 0 · 0 · 0
```

When something spikes, only the spike draws the eye — the rest stays minimal.

## Design rules for the status line

- **Show state, never decisions to make.** A red dot meaning "issue here, click to investigate" is ambient. A list of 12 issues to triage is persistent — it doesn't belong in the status line. Crossing the line floods the ambient channel and trains the human to ignore it.
- **Glance-readable in under one second.** If the human has to parse the indicator to understand it, it's the wrong shape. Use icons + counts, not prose.
- **No interruptive transitions.** Status indicators may change as state changes, but they don't animate, blink, or pop up modals. Ambient = peripheral; interruption is a dashboard's job.
- **Two producers is the working set.** Linter + Kanban counts. A third ambient producer is one too many — the line stops being glanceable when there are more than four to six tokens to parse. New "I want this always visible" requests get evaluated against the existing two, not added alongside.

The status line is the smallest of the UI components by design. Anything that needs more than one line earns its way into one of the others.
