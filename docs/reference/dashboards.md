---
title: Surfaces, Bases, and dashboards
parent: Agents and control
grand_parent: Reference
---

# Surfaces, Bases, and dashboards

Dashboard and Bases inventory for the shipped Obsidian surface. Dashboards are consumers: they render vault state and logs, never write. Space switching is owned by the navigation rail (`_nav.md`), not an Obsidian workspace swap.

---

## Dashboard inventory

| Surface | Dashboard | File | Shows |
| --- | --- | --- | --- |
| Queue | Inbox | `spaces/inbox.md` | Daily attention queue (`projection: queue`), reached from the rail's *Now*: compact in-process Activity first, then `Needs me`. |
| Maintenance | Maintenance | `spaces/maintenance.md` | Weekly structural-debt collection (`projection: maintenance`): drift watch, loose ends, queue state, and new-this-week digest. |
| Space | Library | `spaces/library.md` | Source intake space: reading pipeline, discuss queue, and Catalog papers. |
| Space | Knowledge | `spaces/knowledge.md` | Synthesis space: checked note status, open questions, contradictions, hubs, and patterns. |
| Space | Project | `spaces/project.md` | Project steering space: active projects, refutation-stamp gate, saturation, and project gaps. |
| Maintenance support | Board state | `system/dashboards/board-state.md` | Queue and attention projections for debugging worker state and PI-facing prompts. |
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
| `catalog.base` | `catalog/` | Checked and unchecked `source` Concepts under `catalog/sources/`. |
| `knowledge.base` | `knowledge/views/` | `digest`, `note`, `hub`, and `project` Concepts by home and `check_status`. |
| `capabilities.base` | `capabilities/` | `operation`, `skill`, `mcp`, and `workflow` Concepts by home and `check_status`. |

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
- The audit-log schema fleet-health and audit-log read: [Memory substrates](memory-substrates.md)
- Current Concept types: [Document types](document-types.md)
- Where the dashboards open by default: [Obsidian workspaces](obsidian-workspaces.md)
- Dashboard design rationale: [Dashboards](../explanation/dashboards/README.md)
