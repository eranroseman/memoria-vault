---
title: Surfaces and dashboards
parent: Surfaces
grand_parent: Explanation
nav_order: 1
has_children: true
permalink: /explanation/surfaces/dashboards/
---

# Surfaces and dashboards

The shipped **Inbox** is the file-backed action queue: discrete things that need
you now. The named **dashboards** in this section are planned, consumer-only
optional-adapter views over shipped CLI/read-API data.

The pages in this section explain four kinds of surface: daily attention,
synthesis agenda, structural health, and operational health. The exact
availability and backing sources are in
[Dashboards](../../../reference/analysis-and-surfaces/dashboards.md).

The planned dashboard rail starts with **Now**. In the shipped product, the
file-backed Inbox is the daily action queue; Maintenance is the planned weekly
structural-debt collection behind the health band. Board state is the
worker-debug read over request and attention state, not a shipped dashboard
file. The generated Project gate index (`project-gate-index.md`) is a
deterministic on-disk artifact, not a dashboard view — the separate, planned
Project dashboard in the reference inventory would surface that gate state
(and other project steering signals) over the read API. The
synthesis-vs-structural split is by *actor*: open questions and contradictions
are the **PI's** unfinished thinking; loose ends and Drift watch are the
**Linter operation's** structural debt — kept separate, not collapsed.

## Dashboard map

- [Daily glance](daily-glance.md) — daily attention
- [Synthesis agenda](synthesis-agenda.md) — unfinished thinking
- [Structural health](structural-health.md) — vault integrity
- [Operational health](operational-health.md) — runtime evidence

## Related

- How to operate the shipped workspace: [Using Obsidian](../../../how-to-guides/using-obsidian/README.md)
- Work the daily action queue: [Work the action queue](../../../how-to-guides/inbox/work-the-action-queue.md)
- The primary weekly entry point: [Run the weekly review](../../../how-to-guides/inbox/run-the-weekly-review.md)
