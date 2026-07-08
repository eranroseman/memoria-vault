---
title: Daily glance
parent: Surfaces
nav_order: 11
grand_parent: Explanation
permalink: /explanation/surfaces/dashboards/daily-glance/
---

# Daily glance

What you check at the start of a session to answer "is anything running, and
what needs me today?" The glance starts in the rail's **Now**: the Inbox action
count opens the daily queue, while the health band opens Maintenance.

## Rail Now

The rail is the always-visible 30-second check. It shows the daily action count,
structural drift count, and place counts. Empty is success:
zeroed badges mean there is no daily interruption.

The rail is not a task list and not a vault audit. Click through only when a
count is non-zero.

## Inbox activity and action queue

The Inbox page turns the rail count into work:

| Section | Question |
| --- | --- |
| Activity | Is anything currently pending, running, done, failed, or cancelled? |
| Action queue | What requires a PI decision or action now? |
| Fleeting notes | Which raw PI captures still need processing? |

Activity is status only. Done, failed, and cancelled requests remain inspectable
through the request read API; an actionable attention item appears only when the
PI can do something about it.

## Board-state support

The full board-state dashboard (`system/dashboards/board-state.md`) is the
maintenance/debugging entrypoint for the request and attention read APIs. Use
it when the compact Inbox Activity strip is not enough and you need the exact
CLI commands for queue state.

It is read-only. Runtime queue state lives in SQLite and is surfaced through
`memoria request ...` and `memoria attention ...`; there is no file-backed board
projection to edit.

## Related

- Exact shipped surfaces: [Dashboards](../../../reference/dashboards.md)
- Operating the Inbox: [Work the action queue](../../../how-to-guides/inbox/work-the-action-queue.md)
- Troubleshooting stuck work: [Fix a stuck card](../../../how-to-guides/troubleshooting/fix-stuck-card.md)
