---
title: Surfaces, Bases, and dashboards
parent: Agents and control
grand_parent: Reference
nav_order: 13
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
| Queue | Inbox | `inbox/` | Daily attention queue (`projection: attention`), surfaced by the request/attention commands. |
| Maintenance | Maintenance | `system/dashboards/` | Weekly structural-debt collection: drift watch, loose ends, queue state, and new-this-week digest. |
| Corpus | Library | `works/`, `sources/`, `bibliography.bib` | Source intake, source notes, checked Work bundles, and bibliography projection. |
| Corpus | Knowledge | `notes/`, `hubs/` | Synthesis status, open questions, contradictions, hubs, and patterns. |
| Corpus | Project | `projects/` | Project steering: active projects, refutation-stamp gate, saturation, and project gaps. |
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
[the four-type Concept model with meaning-only frontmatter](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md), and SQLite catalog rows are
governed by the decision that [standalone catalog is the citation authority](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md).

| Base | Lives at | View over |
| --- | --- | --- |
| Optional adapter views | Adapter-owned profile files | Work, source-note, note, hub, and project Concepts by home. Verdicts stay in SQLite/read API. |

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
