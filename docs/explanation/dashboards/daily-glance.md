---
title: Daily glance
parent: Surfaces and dashboards
nav_order: 1
grand_parent: Explanation
permalink: /explanation/dashboards/daily-glance/
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
| Activity | Is anything currently queued, ready, or running? |
| Action queue | What requires a PI decision or action now? |
| Fleeting notes | Which raw PI captures still need processing? |

Activity is status only. Done and blocked tasks leave Activity; a blocked task
creates an actionable attention item only when the PI can do something
about it.

## Board-state support

The full board-state dashboard (`system/dashboards/board-state.md`) is the
maintenance/debugging view over `inbox.base` and `system/board/` worker
projections. Use it when the compact Inbox Activity strip is not enough and you
need the whole board layer.

It is read-only. Editing worker projections does not change runtime queue state.

## Related

- Exact shipped surfaces: [Dashboards](../../reference/dashboards.md)
- Operating the Inbox: [Work the action queue](../../how-to-guides/inbox/work-the-action-queue.md)
- Troubleshooting stuck work: [Fix a stuck card](../../how-to-guides/troubleshooting/fix-stuck-card.md)
