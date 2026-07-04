---
title: Surfaces, Bases, and dashboards
parent: Agents and control
grand_parent: Reference
---

# Surfaces, Bases, and dashboards

Dashboard and view inventory for the standalone workspace. Dashboards are
consumers: they render workspace state and logs, never write. Optional editor
adapters may render the same files, but they do not own state, checks, or
navigation.

---

## Dashboard inventory

| Surface | Dashboard | File | Shows |
| --- | --- | --- | --- |
| Queue | Inbox | `spaces/inbox.md` | Daily attention queue (`projection: queue`), reached from the rail's *Now*: compact in-process Activity first, then `Needs me`. |
| Maintenance | Maintenance | `spaces/maintenance.md` | Weekly structural-debt collection (`projection: maintenance`): drift watch, loose ends, queue state, and new-this-week digest. |
| Space | Library | `spaces/library.md` | Source intake space: reading pipeline, discuss queue, and checked Works. |
| Space | Knowledge | `spaces/knowledge.md` | Synthesis space: checked note status, open questions, contradictions, hubs, and patterns. |
| Space | Project | `spaces/project.md` | Project steering space: active projects, refutation-stamp gate, saturation, and project gaps. |
| Maintenance support | Board state | `system/dashboards/board-state.md` | Queue and attention projections for debugging worker state and PI-facing prompts. |
| Runtime ops | Audit log | `system/dashboards/audit-log.md` | `system/logs/audit.jsonl` — recent writes (each view row-capped, not time-windowed); unhandled denies -> flag. |
| Runtime ops | Eval trend | `system/dashboards/eval-trend.md` | Quarterly vault-eval capability scores (recall@k, support-rate, FAMA-clean) from `system/metrics/eval/runs.jsonl` — diagnostic, never gating. |

The **Surface** column names the space, queue, maintenance collection, or support context where a dashboard is reached.
The explanation site groups the support dashboards by the *kind of attention* they
demand — **Daily glance**, **Synthesis agenda**, **Structural health**, **Operational
health** ([Dashboards](../explanation/dashboards/README.md)).

---

## The Bases views

Obsidian Bases (`.base` files), when present, are optional views over the same
workspace files. Bases are views only; Concept frontmatter is governed by
[ADR-126](../adr/126-four-type-knowledge-model.md), and SQLite catalog rows are
governed by [ADR-124](../adr/124-standalone-catalog-citation-authority.md).

| Base | Lives at | View over |
| --- | --- | --- |
| `knowledge.base` | `knowledge/views/` | Work, note, hub, and project Concepts by home. Verdicts stay in SQLite/read API. |

## Verdict band (Maintenance drift watch)

Maintenance's Drift watch view rolls the Linter operation's detector findings up into
a `PASS` / `REVIEW` / `FAIL` band; the rollup rule and the severity scale it reads
are owned by [Linter: detectors and auto-fix](linter.md#the-detectors).

## Eval metrics (eval-trend)

Per-quarter capability scores, computed into `system/metrics/eval/runs.jsonl`.
The scoring contract is owned by [Vault eval](vault-eval.md).

## Related

- The detectors behind Maintenance drift watch: [Linter: detectors and auto-fix](linter.md)
- The audit-log schema the audit-log dashboard reads: [Memory substrates](memory-substrates.md)
- Current Concept types: [Document types](document-types.md)
- Dashboard design rationale: [Dashboards](../explanation/dashboards/README.md)
