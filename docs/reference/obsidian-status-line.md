---
title: Obsidian status line
parent: Reference
---

# Obsidian status line

No standalone status-line widget ships in the alpha.7 Obsidian surface. The current
ambient glance is the Inbox space: `Needs me`, `Drift watch`, `Loose ends`, and `Board`.
This page records the deferred widget contract so future work does not reinvent the
format.

## Format

Two producers share one line, Linter first then Kanban, separated by `·`:

```text
✓ PASS · Active: 3 · Waiting: 2 · Review: 7 · Retries: 0
```

When everything is quiet:

```text
✓ PASS · Active: 0 · Waiting: 0 · Review: 0 · Retries: 0
```

## Linter segment

Shows the latest Linter verdict (`PASS`, `REVIEW`, or `FAIL`) from `system/metrics/lint-verdict-*.md`, falling back to the current `lint-findings.jsonl` severity mix before metrics have run. Heavy findings still escalate to the `drift-watch` dashboard — they do not expand into the ambient indicator.

## Kanban segment

| Counter | What it counts |
| --- | --- |
| **Active** | Cards in `running` state across all lanes |
| **Waiting** | Cards in `blocked` state |
| **Review** | Cards in `done` with `review_status: requested` (handed off, awaiting human review) |
| **Retries** | Cards in `ready` with `retry_count > 0` |

If this widget ships later, clicking the Kanban counts should open `board-state.md` for
the full view.

## Implementation

The deferred widget would read `system/logs/board-state.jsonl` snapshots written by
`board_export.py` and the latest `lint-verdict` metric note written by
`metrics_aggregate.py`, with a `lint-findings.jsonl` fallback before metrics exist.

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
