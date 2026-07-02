---
title: Always-on VPS design
parent: Design Book
grand_parent: Developers
nav_order: 26
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

## Required properties

| Property | Reason |
| --- | --- |
| One dispatcher per workspace | Two machines dispatching the same request queue can race on request state and produce conflicting audit rows. |
| Desktop owns review and optional reference-manager UI | The human review surface and any desktop-only reference tooling stay local to the PI's machine. |
| VPS owns scheduled CLI invocations and dispatch | Scheduled work needs an always-awake host. |
| Workspace files sync between machines | The PI must see the results locally, while the VPS can process background work. |
| Worker-generated projections avoid mid-transfer reads | The ingest path depends on stable source/citekey metadata; partial sync is a real failure mode. |
| Audit rows remain content-free and append-only | Multi-machine topology must not weaken the audit-memory contract. |

## Boundary

| Component | Required owner |
| --- | --- |
| Review UI and optional reference-manager UI | Desktop |
| `memoria workspace run` and scheduled CLI commands | VPS |
| qmd index for background work | VPS |
| Co-PI query flow | Either desktop or VPS through explicit CLI/API invocation |
| Runtime workspace files | Synced between desktop and VPS |

The owner split above is a boundary, not an install recipe. Platform details stay in the implementation issue until the topology is proven.

## Validation before support

Support requires one live proof: a desktop capture syncs to the VPS, processes
through ingest, records policy-audited writes, and syncs the resulting catalog
and attention state back to the desktop while desktop scheduled jobs stay
disabled. Missing heartbeats must surface as an operator-visible failure, not
silent drift.

## Failure modes to design against

| Failure mode | Design response |
| --- | --- |
| Host sleeps through a timer | Put dispatch on an always-on host rather than a laptop. |
| User services die on logout | The VPS runtime must keep user timers alive across SSH logout. |
| Secrets drift between hosts | Provider and optional-adapter config must be copied through an explicit operator-owned secret process. |
| Two dispatchers run at once | The topology requires a single active dispatcher per vault. |
| Bibliography projection sync is partial | `references.bib` needs a worker-owned regeneration path, not a half-written sync read. |

## Related

- Local install prerequisite: [Quickstart](../how-to-guides/setup/quickstart.md)
- The topology trade-offs and dispatcher rule: [Deployment](../explanation/deployment.md)
- Failure lookup table: [Failure modes](../reference/failure-modes.md)
