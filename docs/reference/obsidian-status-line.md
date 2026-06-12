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

A Dataview inline query in a pinned note. The query reads from a periodically-refreshed `board-state.jsonl` snapshot `board_export.py` writes, or polls the Hermes API (port 8642). No standard implementation is shipped — human setups vary.

## Constraints

| Constraint | Value |
| --- | --- |
| Content | State only (counts), never decisions or triage lists — those escalate to a dashboard |
| Rendering | Icons + counts only, no prose; glance-readable in under one second |
| Motion | No animation or transitions (ambient means peripheral) |
| Producers | Two maximum — Linter + Kanban |

Why the line is shaped this way is explained in [The status line](../explanation/obsidian/the-status-line.md).

## Related

- Why an ambient line rather than a dashboard: [The status line](../explanation/obsidian/the-status-line.md)
- The restraint principle it embodies: [Visual-style discipline](../explanation/obsidian/visual-discipline.md)
- Where the Kanban counts expand: [Dashboards](dashboards.md)
