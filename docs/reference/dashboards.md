---
title: Dashboards
parent: Reference
---

# Dashboards

The eleven dashboards shipped in `system/dashboards/` ([src/system/dashboards/](../../src/system/dashboards)) and the Bases views behind them. Dashboards are browsable **health views** — where things stand; the Inbox is the **action queue** — discrete things that need you now. All are Dataview / Bases consumers: they render existing vault state and logs, never write, and a healthy vault shows them near-empty.

Two changes from v0.1.0-alpha.1: **daily-health was absorbed into the homepage** (`home.md` carries the above-fold glance — there is no `daily-health.md` anymore), and **board-state is now the Inbox board** — a thin page embedding `inbox.base`.

---

## Dashboard inventory

| Surface | Dashboard | File | Shows |
| --- | --- | --- | --- |
| Home | Board state | `board-state.md` | The Inbox board (embeds `inbox.base` — "Needs me" = cards in `proposed`) plus live worker cards from `system/board/`. |
| Library | Reading pipeline | `reading-pipeline.md` | Sources at `lifecycle: proposed` awaiting reading & distillation + claims by maturity. |
| Library | Discuss queue | `discuss-queue.md` | Source notes at `lifecycle: provisional` — read but not yet distilled; worth a co-PI pass. |
| Library / Project | Open questions | `open-questions.md` | `current` claims with zero inbound links — the unconnected synthesis backlog. |
| Library / Project | Contradictions | `contradictions.md` | `current` claims carrying a `links.contradicts` note link — open tensions. |
| Maintenance | Drift watch | `drift-watch.md` | Open `flag`/`alert` cards in `proposed` — active/imminent structural drift; HIGH/`alert` findings also push to Home. |
| Maintenance | Loose ends | `loose-ends.md` | Notice-loudness `flag` cards in `proposed` — low-stakes structural debt batched for the weekly pass. |
| Maintenance | Weekly review | `weekly-review.md` | The Friday aggregator (multi-section). |
| Agent-ops | Audit log | `audit-log.md` | `system/logs/audit.jsonl`, current week; unhandled denies → flag. |
| Agent-ops | Fleet health | `fleet-health.md` | Per-lane trust score / operational rollup from `system/metrics/`. |
| Agent-ops | Eval trend | `eval-trend.md` | Quarterly vault-eval capability scores (recall@k, support-rate, FAMA-clean) from `system/metrics/eval/runs.jsonl` — diagnostic, never gating. |

---

## The Bases views

Obsidian Bases (`.base` files) are the database views the dashboards and workspaces lean on ([ADR-49](../adr/49-catalog-in-bases-linter-monitor.md)). Bases are views; the notes are the source of truth.

| Base | Lives at | View over |
| --- | --- | --- |
| `catalog.base` | `catalog/` | The Catalog — entity records by type (papers, people, organizations, venues, datasets, repositories), `lifecycle != archived`. |
| `inbox.base` | `inbox/` | The Inbox board — cards grouped by type; "Needs me" = `proposed`; converges to empty. |
| `claims.base` | `system/dashboards/` | Claims by maturity. |
| `sources.base` | `system/dashboards/` | Source notes by lifecycle. |
| `fleeting.base` | `system/dashboards/` | Fleeting notes awaiting promote-or-discard. |
| `patterns.base` | `system/patterns/` | The pattern library by mode and lifecycle. |

---

## Verdict band (drift-watch)

Rollup of the Linter engine's detectors:

| Band | Condition | Effect |
| --- | --- | --- |
| `PASS` | Only LOW findings (or none) | — |
| `REVIEW` | Any HIGH or MEDIUM finding, no CRITICAL | Advisory |
| `FAIL` | Any CRITICAL finding | Scheduled work pauses until resolved |

## Trust score (fleet-health)

A 0–100 composite per lane, computed by [src/.memoria/mcp/metrics_aggregate.py](../../src/.memoria/mcp/metrics_aggregate.py) into `system/metrics/`. Inputs: audit deny rate, structural-drift incidents, secret-field access attempts, retry rate, success rate, and accept/reject ratios on lanes producing proposals. Bands: **90+ healthy · 70–89 watch · < 70 act**. Suggestion-ratio extremes both down-weight: accept > ~90% = rubber-stamping; < ~20% = candidate scoring needs tuning.

## Eval metrics (eval-trend)

Per-quarter capability scores, computed by the deterministic scorer [src/.memoria/engines/sweeps/eval_score.py](../../src/.memoria/engines/sweeps/eval_score.py) into `system/metrics/eval/runs.jsonl` ([ADR-11](../adr/11-vault-eval-maintenance.md)). Each metric is 0–1, higher is better: **recall@k** (gold citekeys in the top-k retrieved), **support-rate** (cited evidence resolving to real catalog records), **FAMA-clean** (no superseded/archived claim reused). A gold task whose card reported no machine-readable result shows as **unscored** — never a faked score. Diagnostic, not gating: a dip informs the PI; it does not pause scheduled work. Full contract: [Vault eval](vault-eval.md).

---

## Design conventions (apply to all dashboards)

- **One decision per dashboard** — each surfaces a single decision type.
- **Empty is success** — a healthy vault shows near-empty tables.
- **Sort by decision type** — queues oldest-first; logs newest-first.
- **Graceful degradation** — a missing log or plugin shows an explanatory placeholder, never an error.

The reasoning behind these conventions (and the synthesis-vs-structural actor split) is in [Dashboards](../explanation/dashboards/README.md).

---

## Related

- The detectors behind drift-watch: [Linter: detectors and auto-fix](linter.md)
- The audit-log schema fleet-health and audit-log read: [Memory substrates](memory.md)
- The card types the Inbox board groups: [Note types](note-types.md)
- Where the dashboards open by default: [Obsidian workspaces](obsidian-workspaces.md)
