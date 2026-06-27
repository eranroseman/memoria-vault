---
title: Dashboards
parent: Reference
---

# Dashboards

The primary dashboards are the three durable space notes under `spaces/`
(`src/spaces`): Library, Knowledge, and Project. The Inbox queue (`spaces/inbox.md`,
`type: queue`) and Maintenance collection (`spaces/maintenance.md`, `type: maintenance`)
sit alongside them by cadence: daily action vs weekly structural debt. Both are reached
from the navigation rail's **Now**. Five read-only system dashboards and the
claim/source/fleeting Bases live under `system/dashboards/` (`src/system/dashboards`);
other Bases live beside their data folders. Space
switching is owned by the navigation rail (`_nav.md`), not an Obsidian workspace swap.
All dashboards are Dataview / Bases consumers: they render existing vault state and
logs, never write, and a healthy vault shows action queues near-empty.

The daily glance starts in the rail's **Now**: action count opens the Inbox queue,
while the health band opens Maintenance and Fleet health. **Board-state is the Inbox
board** — a thin page embedding `inbox.base`.

No standalone status-line widget ships in the current Obsidian surface. The rail health
band is the ambient glance for structural and fleet health; the Inbox queue stays the
action surface.

---

## Dashboard inventory

| Surface | Dashboard | File | Shows |
| --- | --- | --- | --- |
| Queue | Inbox | `spaces/inbox.md` | Daily attention queue (`type: queue`), reached from the rail's *Now*: compact in-process Activity first, then `Needs me`, then fleeting processing. |
| Maintenance | Maintenance | `spaces/maintenance.md` | Weekly structural-debt collection (`type: maintenance`): drift watch, loose ends, board, and new-this-week digest. |
| Space | Library | `spaces/library.md` | Source intake space: reading pipeline, discuss queue, and Catalog papers. |
| Space | Knowledge | `spaces/knowledge.md` | Synthesis space: claims by maturity, open questions, contradictions, hubs, and patterns. |
| Space | Project | `spaces/project.md` | Project steering space: active projects, refutation-stamp gate, saturation, and project gaps. |
| Maintenance support | Board state | `system/dashboards/board-state.md` | The full Inbox board (embeds `inbox.base` — "Needs me" = proposed `candidate` / `gap` / `work-prompt` action cards, with title/action merged into the clickable row label and findings visible in Maintenance views) plus worker-card projections from `system/board/`. |
| Agent-ops | Audit log | `system/dashboards/audit-log.md` | `system/logs/audit.jsonl` — recent writes (each view row-capped, not time-windowed); unhandled denies -> flag. |
| Agent-ops | Fleet health | `system/dashboards/fleet-health.md` | Per-lane trust score / operational rollup from `system/metrics/`. |
| Agent-ops | Eval trend | `system/dashboards/eval-trend.md` | Quarterly vault-eval capability scores (recall@k, support-rate, FAMA-clean) from `system/metrics/eval/runs.jsonl` — diagnostic, never gating. |
| Agent-ops | Skill state | `system/dashboards/skill-state.md` | Which skills are active in which lane, read live from `.memoria/lane-overrides/` + `.memoria/profiles/*/skills/`; mismatches surface as consistency-check rows ([ADR-43](../adr/43-skill-governance.md)). |

The **Surface** column names the space, queue, maintenance collection, or support context where a dashboard is reached.
The explanation site groups the support dashboards by the *kind of attention* they
demand — **Daily glance**, **Synthesis agenda**, **Structural health**, **Operational
health** ([Dashboards](../explanation/dashboards/README.md)).

---

## The Bases views

Obsidian Bases (`.base` files) are the database views the dashboards and space notes lean on ([ADR-49](../adr/49-catalog-in-bases-linter-monitor.md)). Bases are views; the notes are the source of truth.

| Base | Lives at | View over |
| --- | --- | --- |
| `catalog.base` | `catalog/` | The Catalog — entity records by type (papers, people, organizations, venues, datasets, repositories), `lifecycle != archived`. |
| `inbox.base` | `inbox/` | The Inbox board — cards grouped by type; "Needs me" = proposed `candidate` / `gap` / `work-prompt` action cards; the clickable row label merges title/action, while drift views expose findings; converges to empty. |
| `board.base` | `system/board/` | Worker-card projections by lane/state, mirrored from Hermes board state; the Inbox embeds only the in-process Activity view. |
| `claims.base` | `system/dashboards/` | Claims by maturity. |
| `sources.base` | `system/dashboards/` | Source notes by lifecycle. |
| `fleeting.base` | `system/dashboards/` | Fleeting notes awaiting promote-or-discard. |
| `hubs.base` | `notes/hubs/` | Hub notes by topic cluster and lifecycle. |
| `projects.base` | `projects/` | Project notes by output mode, refutation stamp, thesis state, saturation, and open gaps. |
| `patterns.base` | `system/patterns/` | The pattern library by mode and lifecycle. |
| `worklists.base` | `system/worklists/` | Batch screening rows grouped by worklist, decision, or group; rows are `worklist-item` notes and one aggregate Inbox prompt points here. |

## Verdict band (Maintenance drift watch)

Maintenance's Drift watch view rolls the Linter operation's detector findings up into
a `PASS` / `REVIEW` / `FAIL` band; the rollup rule and the severity scale it reads
are owned by [Linter: detectors and auto-fix](linter.md#the-detectors).

## Trust score (fleet-health)

A 0–100 composite per lane, computed into `system/metrics/`. The formula and
bands are owned by [Fleet metrics](fleet-metrics.md).

## Eval metrics (eval-trend)

Per-quarter capability scores, computed into `system/metrics/eval/runs.jsonl`.
The scoring contract is owned by [Vault eval](vault-eval.md).

## Related

- The detectors behind Maintenance drift watch: [Linter: detectors and auto-fix](linter.md)
- The audit-log schema fleet-health and audit-log read: [Memory substrates](memory.md)
- The card types the Inbox board groups: [Document types](document-types.md)
- Where the dashboards open by default: [Obsidian workspaces](obsidian-workspaces.md)
- Dashboard design rationale: [Dashboards](../explanation/dashboards/README.md)
