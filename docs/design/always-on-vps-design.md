---
title: Always-on VPS design
parent: Design Book
grand_parent: Developers
nav_order: 24
---

# Always-on VPS design

> **Status — deferred.** The supported install path is documented around the `local-only` pattern; the `always-on` topology is designed but not validated end-to-end (tracked in [#383](https://github.com/eranroseman/memoria-vault/issues/383); design: [Deployment options](../explanation/deployment/deployment-options.md), [Multi-machine deployment (topologies and secondary-device patterns)](../adr/63-multi-machine-deployment.md)). This page records the intended topology and validation shape; it is not a supported setup guide.

The always-on design moves Hermes from local WSL2 to a persistent VPS so scheduled crons can run overnight, board cards can process unattended, and the system can stay reachable from more than one device. The VPS becomes the **one dispatcher** for the vault; the desktop keeps Obsidian and Zotero; the vault files sync between them.

## Design intent

The topology exists to solve one specific problem: a laptop or desktop is not always awake when Memoria's maintenance loop should run. A persistent host gives the board dispatcher, sweeps, lint, metrics, eval dispatch, and qmd index a stable place to live.

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

## Intended topology

| Component | Intended home |
| --- | --- |
| Obsidian and Zotero | Desktop |
| Hermes dispatch and scheduled crons | VPS |
| qmd index for background work | VPS |
| Co-PI conversation | Either desktop or VPS over an explicit ACP launch path |
| Runtime vault files | Synced between desktop and VPS |

The design assumes an Ubuntu-class VPS and a desktop that can reach it over SSH, but those platform details are validation concerns, not a supported setup contract yet.

## Validation shape

The topology is not ready until a future implementation issue proves all of these behaviors end-to-end:

- The VPS registers the five `memoria-*` profiles and the maintenance crons.
- The desktop crons are disabled while the VPS crons are active.
- A desktop capture can sync to the VPS, process through ingest, and sync the resulting Catalog entity and Inbox card back to the desktop.
- `system/logs/audit.jsonl` records the VPS-side gated writes.
- `system/logs/cron-heartbeat.jsonl` shows fresh rows for scheduled jobs after their expected cadence.
- A stale or missing heartbeat leads to an operator-visible failure path, not silent drift.

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
- The topology trade-offs and dispatcher rule: [Deployment options](../explanation/deployment/deployment-options.md)
- Profile configuration: [Configure a profile](../how-to-guides/hermes-agent/configuration.md)
- Failure lookup table: [Failure modes](../reference/failure-modes.md)
