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

The planned dashboard rail starts with **Now**. Today, the file-backed Inbox and
`memoria attention list` are the daily action queue; Maintenance is the planned
weekly structural-debt collection behind the health band.
Board state is the worker-debug view over request and attention state, surfaced
through `memoria request list` and `memoria attention list`, not a shipped
dashboard file. The generated Project gate index (`project-gate-index.md`) is a
deterministic on-disk artifact, not a dashboard view — the separate, planned
Project dashboard in the reference inventory would surface that gate state
(and other project steering signals) over the read API. The synthesis-vs-structural split is by *actor*:
open-questions and contradictions are the **PI's** unfinished thinking; loose-ends and
drift-watch are the **Linter operation's** structural debt — kept separate, not collapsed.

## Related

- How to operate the shipped workspace: [Using Obsidian](../../../how-to-guides/using-obsidian/README.md)
- The primary weekly entry point: [Run the weekly review](../../../how-to-guides/inbox/run-the-weekly-review.md)
