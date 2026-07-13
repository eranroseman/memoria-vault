---
title: Surfaces and dashboards
parent: Analysis and surfaces
nav_order: 5
grand_parent: Reference
---

# Surfaces and dashboards

Dashboard and view inventory for the standalone workspace. Dashboards are
consumers: they render workspace state and logs, never write. The standalone
baseline does not ship `system/dashboards/*.md`; views are CLI/read-API surfaces and optional
editor adapters may render them later without owning state, checks, or
navigation.

---

## Dashboard inventory

| Surface | View | Availability | Backing surface | Shows |
| --- | --- | --- | --- | --- |
| Queue | Inbox | Shipped CLI/read API | `inbox/` | Daily attention queue (`projection: attention`), surfaced by the request/attention commands. |
| Maintenance | Maintenance | Planned optional adapter | request/attention/linter reads | Weekly structural-debt collection: drift watch, loose ends, queue state, and new-this-week digest. |
| Corpus | Library | Planned optional adapter | `digests/`, `fulltexts/`, `bibliography.bib` | Source intake, checked digests, generated full text, and bibliography projection. |
| Corpus | Knowledge | Planned optional adapter | `notes/`, `hubs/` | Synthesis status, open questions, contradictions, hubs, and patterns. |
| Corpus | Project | Planned optional adapter | `projects/` | Project steering: active projects, refutation-stamp gate, saturation, and project gaps. |
| Maintenance support | Board state | Shipped CLI/read API | `memoria request list` / `memoria attention list` | Queue and attention projections for debugging worker state and PI-facing prompts. |
| Runtime ops | Audit log | Planned view; log shipped | `system/logs/audit.jsonl` | Recent writes; an adapter may render row-capped views. |
| Runtime ops | Eval trend | Planned view; metric log shipped | `system/metrics/eval/runs.jsonl` | Quarterly vault-eval capability scores (recall@k, support-rate, FAMA-clean) — diagnostic, never gating. |

The **Surface** column names the corpus home, queue, maintenance collection, or
support context where a shipped read or planned view belongs.
The explanation site groups the support dashboards by the *kind of attention* they
demand — **Daily glance**, **Synthesis agenda**, **Structural health**, **Operational
health** ([Dashboards](../../explanation/surfaces/dashboards/README.md)).

---

## Optional editor views

Optional editor views, when present, read the same workspace files. They are
views only; Concept frontmatter is governed by the YAML schemas under
`.memoria/schemas/`, and SQLite catalog rows are
governed by the decision that [standalone catalog is the citation authority](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md).

| View | Lives at | View over |
| --- | --- | --- |
| Optional adapter views | Adapter-owned view files | Digest, fulltext, note, hub, and project documents by home. Verdicts stay in SQLite/read API. |

## Planned verdict band (Maintenance drift watch)

The Linter already computes a `PASS` / `REVIEW` / `FAIL` verdict. A planned
Maintenance view may render that verdict as a Drift watch band; the rollup rule
and severity scale are owned by [Linter: detectors and auto-fix](linter.md#the-detectors).

## Eval metrics (eval-trend)

Per-quarter capability scores, computed into `system/metrics/eval/runs.jsonl`.
The scoring contract is owned by [Vault eval](vault-eval.md).

## Related

- The detectors behind Maintenance drift watch: [Linter: detectors and auto-fix](linter.md)
- The audit-log schema a planned audit-log view may read: [Memory substrates](../pipelines-and-io/memory-substrates.md)
- Current Concept types: [Document types](../data-model/document-types.md)
- Dashboard design rationale: [Dashboards](../../explanation/surfaces/dashboards/README.md)
