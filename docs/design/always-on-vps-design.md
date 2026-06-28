---
title: Always-on VPS design
parent: Design Book
grand_parent: Developers
nav_order: 26
---

# Always-on VPS design

> **Status — deferred.** The supported install path is local-only. Always-on deployment is not a supported setup path until [#383](https://github.com/eranroseman/memoria-vault/issues/383) validates it end to end. This page records the design boundary; the topology proposal lives in [ADR-63](../adr/63-multi-machine-deployment.md).

The always-on idea moves Hermes from a sleep-prone desktop to a persistent host so scheduled crons can run overnight. The design is acceptable only if it preserves Memoria's single-dispatcher rule and does not turn the vault into a multi-writer system.

## Design intent

The topology exists to solve one problem: a laptop or desktop is not always awake when Memoria's maintenance loop should run. A persistent host gives scheduled maintenance a stable place to live.

The design does **not** make Memoria multi-writer. It preserves the solo-researcher premise by keeping exactly one machine responsible for dispatch and cron writes. Obsidian remains the human interface on the desktop, and the VPS is infrastructure: it runs deterministic maintenance and background lane work against the synced runtime vault.

## Required properties

| Property | Reason |
| --- | --- |
| One dispatcher per vault | Two machines dispatching the same board can race on card state and produce conflicting audit rows. |
| Desktop owns Obsidian and Zotero | The human review surface and bibliographic manager stay local to the PI's machine. |
| VPS owns crons and dispatch | Scheduled work needs an always-awake host. |
| Vault files sync between machines | The PI must see the results locally, while the VPS can process background work. |
| `.memoria/memoria.bib` distribution avoids mid-transfer reads | The ingest path depends on stable citekey metadata; partial sync is a real failure mode. |
| Audit rows remain content-free and append-only | Multi-machine topology must not weaken the audit-memory contract. |

## Boundary

| Component | Required owner |
| --- | --- |
| Obsidian and Zotero | Desktop |
| Hermes dispatch and scheduled crons | VPS |
| qmd index for background work | VPS |
| Co-PI conversation | Either desktop or VPS over an explicit ACP launch path |
| Runtime vault files | Synced between desktop and VPS |

The owner split above is a boundary, not an install recipe. Platform details stay in ADR-63 and the implementation issue until the topology is proven.

## Validation before support

Support requires one live proof: a desktop capture syncs to the VPS, processes through ingest, records policy-audited writes, and syncs the resulting Catalog and Inbox state back to the desktop while desktop crons stay disabled. Missing heartbeats must surface as an operator-visible failure, not silent drift.

## Failure modes to design against

| Failure mode | Design response |
| --- | --- |
| Host sleeps through a timer | Put dispatch on an always-on host rather than a laptop. |
| User services die on logout | The VPS runtime must keep user timers alive across SSH logout. |
| Secrets drift between profiles | Profile redeploy remains the supported way to propagate `.env` changes. |
| Two dispatchers run at once | The topology requires a single active dispatcher per vault. |
| Bibliography sync is partial | `.memoria/memoria.bib` needs a stable distribution path, not a half-written sync read. |

## Related

- Local install prerequisite: [Quickstart](../how-to-guides/setup/quickstart.md)
- The topology trade-offs and dispatcher rule: [Deployment](../explanation/deployment.md)
- Profile configuration: [Configure a profile](../how-to-guides/hermes-agent/configure-a-profile.md)
- Failure lookup table: [Failure modes](../reference/failure-modes.md)
