---
title: Always-on VPS design
parent: Deployment rationale
grand_parent: Design rationale
nav_order: 1
---

# Always-on VPS design

> **Status — deferred.** The supported install path is local-only. Always-on deployment is not a supported setup path until [#383](https://github.com/eranroseman/memoria-vault/issues/383) validates it end to end and a new deployment decision accepts it. This page records design notes only; it is not an install recipe.

The always-on idea moves scheduled Memoria CLI/runtime work from a sleep-prone
desktop to a persistent host. The design is acceptable only if it preserves
Memoria's single-dispatcher rule and does not turn the workspace into a
multi-writer system.

## Design intent

The topology exists to solve one problem: a laptop or desktop is not always awake when Memoria's maintenance loop should run. A persistent host gives scheduled maintenance a stable place to live.

The design does **not** make Memoria multi-writer. It preserves the
solo-researcher premise by keeping exactly one machine responsible for queued
dispatch and scheduled writes. The PI's desktop remains the human review
surface, and the VPS is infrastructure: it runs deterministic maintenance and
background operation requests against the synced runtime workspace.

## Required boundary

The topology only works if one host owns dispatch for a workspace. Two machines
running the same queue would race request state and audit rows. The desktop
keeps the human review surface and optional desktop-only tools; the persistent
host owns scheduled CLI work. Synced files are just the substrate between them,
not permission to run two writers.

Platform details stay in the implementation issue until the topology is proven.

## Validation before support

Support requires one live proof: a desktop capture syncs to the VPS, processes
through ingest, records policy-audited writes, and syncs the resulting catalog
and attention state back to the desktop while desktop scheduled jobs stay
disabled. Missing heartbeats must surface as an operator-visible failure, not
silent drift.

## Failure modes to design against

The design must survive sleeping desktops, logout-killed services, secret drift,
double dispatch, and partial synced projections. Those failures are why the
topology remains deferred: each needs a live proof before support.

## Related

- Local install prerequisite: [Quickstart](../../../how-to-guides/setup/quickstart.md)
- The topology trade-offs and dispatcher rule: [Deployment](../../deployment/README.md)
- Failure lookup table: [Failure modes](../../../reference/system/failure-modes.md)
