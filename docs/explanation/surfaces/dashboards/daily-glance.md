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

The navigator rail is planned for an optional dashboard adapter. Its **Now**
band would be a compact attention signal where empty is success.

The shipped file-backed Inbox currently provides that signal. The planned rail
is a pointer to the few places where daily attention may be needed, not a task
list or vault audit.

## Inbox activity and action queue

The shipped Inbox provides the signal today. Attention items and request
execution state are kept separate so that activity reads as status, never as
an action item; an optional Inbox page may combine the two views without
merging the states. Where each state lives is catalogued in
[Dashboards](../../../reference/analysis-and-surfaces/dashboards.md).

## Board-state support

A planned Board dashboard may combine the maintenance/debugging reads under a
compact Inbox Activity strip. It is read-only: there is no file-backed board
dashboard to edit, so the board can never become a second place where state
is authored.

## Related

- Availability and backing surfaces: [Dashboards](../../../reference/analysis-and-surfaces/dashboards.md)
- Operating the Inbox: [Work the action queue](../../../how-to-guides/inbox/work-the-action-queue.md)
- Troubleshooting stuck work: [Fix a stuck request](../../../how-to-guides/troubleshooting/fix-stuck-card.md)
