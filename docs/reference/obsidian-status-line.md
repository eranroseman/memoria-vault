---
title: Obsidian status line
parent: Reference
---

# Obsidian status line

The ambient indicator showing Linter findings and Kanban queue counts. Rendered as a Dataview widget pinned in `home.md`, not the OS status bar (which Dataview cannot write to).

## Format

Two producers share one line, Linter first then Kanban, separated by `·`:

```text
✓ Schema valid · 2 broken links · Active: 3 · Waiting: 2 · Review: 7 · Retries: 0
```

When everything is quiet:

```text
✓ · 0 · 0 · 0 · 0
```

## Linter segment

Shows lightweight findings from the last lint pass: schema validity, broken link count, oversized notes. Heavy findings (schema migrations, structural drift) escalate to the `drift-watch` dashboard — they don't belong in the ambient indicator.

## Kanban segment

| Counter | What it counts |
| --- | --- |
| **Active** | Cards in `running` state across all lanes |
| **Waiting** | Cards in `blocked` state |
| **Review** | Cards in `done` with `review_status: requested` (handed off, awaiting human review) |
| **Retries** | Cards returned to `ready` after a recoverable failure |

Click anywhere in the Kanban counts to open `board-state.md` for the full view.

## Implementation

A Dataview inline query in a pinned note. The query reads from a periodically-refreshed `board-state.jsonl` snapshot the Kanban dispatcher writes, or polls the Hermes API (port 8642). No standard implementation is shipped — human setups vary.

## Design rules

- **Show state, not decisions.** A count is ambient. A list of items to triage belongs in a dashboard.
- **Glance-readable in under one second.** Icons + counts only; no prose.
- **No animation or transitions.** Ambient means peripheral; blinking or popping up breaks that.
- **Two producers maximum.** Linter + Kanban is the working set. A third ambient producer makes the line unreadable.
