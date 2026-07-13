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

Today, use `memoria attention list --workspace .` for that signal. The planned
rail is a pointer to the few places where daily attention may be needed, not a
task list or vault audit.

## Inbox activity and action queue

The shipped Inbox state is file-backed: attention items live under `inbox/` and
the read API projects those files into table/card views. Request execution state
lives separately in SQLite. An optional Inbox page may combine those views;
activity remains status, not an action item.

## Board-state support

A planned Board dashboard may combine the maintenance/debugging reads under a
compact Inbox Activity strip.

It is read-only. Runtime request state lives in SQLite; attention lives in
`inbox/*.md` and is projected by the read API. Both are surfaced through
`memoria request ...` and `memoria attention ...`; there is no file-backed board
dashboard to edit.

## Related

- Availability and backing surfaces: [Dashboards](../../../reference/analysis-and-surfaces/dashboards.md)
- Operating the Inbox: [Work the action queue](../../../how-to-guides/inbox/work-the-action-queue.md)
- Troubleshooting stuck work: [Fix a stuck request](../../../how-to-guides/troubleshooting/fix-stuck-card.md)
