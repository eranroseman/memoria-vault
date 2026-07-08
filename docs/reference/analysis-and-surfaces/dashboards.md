---
title: Surfaces, Bases, and dashboards
parent: Analysis and surfaces
nav_order: 5
grand_parent: Reference
---

# Surfaces, Bases, and dashboards

Dashboard and view inventory for the standalone workspace. Dashboards are
consumers: they render workspace state and logs, never write. Alpha.20 does not
ship `system/dashboards/*.md`; views are CLI/read-API surfaces and optional
editor adapters may render them later without owning state, checks, or
navigation.

---

## Dashboard inventory

| Surface | View | Backing surface | Shows |
| --- | --- | --- | --- |
| Queue | Inbox | `inbox/` | Daily attention queue (`projection: attention`), surfaced by the request/attention commands. |
| Maintenance | Maintenance | request/attention/linter reads | Weekly structural-debt collection: drift watch, loose ends, queue state, and new-this-week digest. |
| Corpus | Library | `digests/`, `fulltexts/`, `bibliography.bib` | Source intake, checked digests, generated full text, and bibliography projection. |
| Corpus | Knowledge | `notes/`, `hubs/` | Synthesis status, open questions, contradictions, hubs, and patterns. |
| Corpus | Project | `projects/` | Project steering: active projects, refutation-stamp gate, saturation, and project gaps. |
| Maintenance support | Board state | `memoria request list` / `memoria attention list` | Queue and attention projections for debugging worker state and PI-facing prompts. |
| Runtime ops | Audit log | `system/logs/audit.jsonl` | Recent writes (each view row-capped, not time-windowed); unhandled denies -> flag. |
| Runtime ops | Eval trend | `system/metrics/eval/runs.jsonl` | Quarterly vault-eval capability scores (recall@k, support-rate, FAMA-clean) — diagnostic, never gating. |

The **Surface** column names the space, queue, maintenance collection, or support context where a dashboard is reached.
The explanation site groups the support dashboards by the *kind of attention* they
demand — **Daily glance**, **Synthesis agenda**, **Structural health**, **Operational
health** ([Dashboards](../../explanation/surfaces/dashboards/README.md)).

---

## The Bases views

Obsidian Bases (`.base` files), when present, are optional views over the same
workspace files. Bases are views only; Concept frontmatter is governed by
the YAML schemas under `.memoria/schemas/`, and SQLite catalog rows are
governed by the decision that [standalone catalog is the citation authority](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md).

| Base | Lives at | View over |
| --- | --- | --- |
| Optional adapter views | Adapter-owned profile files | Digest, fulltext, note, hub, and project documents by home. Verdicts stay in SQLite/read API. |

## Verdict band (Maintenance drift watch)

Maintenance's Drift watch view rolls the Linter operation's detector findings up into
a `PASS` / `REVIEW` / `FAIL` band; the rollup rule and the severity scale it reads
are owned by [Linter: detectors and auto-fix](linter.md#the-detectors).

## Eval metrics (eval-trend)

Per-quarter capability scores, computed into `system/metrics/eval/runs.jsonl`.
The scoring contract is owned by [Vault eval](vault-eval.md).

## Related

- The detectors behind Maintenance drift watch: [Linter: detectors and auto-fix](linter.md)
- The audit-log schema the audit-log dashboard reads: [Memory substrates](../pipelines-and-io/memory-substrates.md)
- Current Concept types: [Document types](../data-model/document-types.md)
- Dashboard design rationale: [Dashboards](../../explanation/surfaces/dashboards/README.md)
