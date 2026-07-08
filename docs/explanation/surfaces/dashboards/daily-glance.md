---
title: Daily glance
parent: Surfaces and dashboards
nav_order: 1
grand_parent: Surfaces
permalink: /explanation/surfaces/dashboards/daily-glance/
---

# Daily glance

Daily glance answers one question: "does anything need the PI now?" It exists
because the vault can contain many useful views, but daily work needs one
low-noise signal.

## Rail Now

The rail is the compact attention signal. Empty is success: zeroed badges mean
there is no daily interruption.

The rail is not a task list and not a vault audit. It is a pointer to the few
places where daily attention may be needed.

## Inbox activity and action queue

The Inbox page expands the daily signal into request status, attention, and raw
captures. Activity is status only; an actionable attention item appears only
when the PI can do something about it.

## Board-state support

The full board-state dashboard is the maintenance/debugging view under the
compact Inbox Activity strip.

It is read-only. Runtime queue state lives in SQLite and is surfaced through
`memoria request ...` and `memoria attention ...`; there is no file-backed board
projection to edit.

## Related

- Exact shipped surfaces: [Dashboards](../../../reference/analysis-and-surfaces/dashboards.md)
- Operating the Inbox: [Work the action queue](../../../how-to-guides/inbox/work-the-action-queue.md)
- Troubleshooting stuck work: [Fix a stuck request](../../../how-to-guides/troubleshooting/fix-stuck-card.md)
