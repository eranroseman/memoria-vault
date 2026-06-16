---
title: Dashboards
parent: Reference
---

# Dashboards

The dashboards shipped in `system/dashboards/` (`src/system/dashboards`) and the Bases views behind them. The three gate dashboards — Desk, Library, and Studio — are workspace landing surfaces; the rest are drill-down health or object views. All are Dataview / Bases consumers: they render existing vault state and logs, never write, and a healthy vault shows action queues near-empty.

Two changes from v0.1.0-alpha.1: **daily-health was absorbed into the homepage** (`home.md` carries the above-fold glance — there is no `daily-health.md` anymore), and **board-state is now the Inbox board** — a thin page embedding `inbox.base`.

---

## Dashboard inventory

| Surface | Dashboard | File | Shows |
| --- | --- | --- | --- |
| Desk | Desk gate | `desk.md` | Action-first landing surface: the Inbox `Needs me` queue, capture/delegate/resolve commands, and worker state. |
| Desk | Board state | `board-state.md` | The full Inbox board (embeds `inbox.base` — "Needs me" = cards in `proposed`, with the card's `action`/`finding` visible) plus live worker cards from `system/board/`. |
| Library | Library gate | `library.md` | Object-first landing surface: source notes, Catalog papers, and claims by maturity. |
| Library | Reading pipeline | `reading-pipeline.md` | Object-first Bases view: source notes at `lifecycle: proposed` awaiting reading & distillation + current claims by maturity. |
| Library | Discuss queue | `discuss-queue.md` | Source notes at `lifecycle: provisional` — read but not yet distilled; worth a Co-PI pass. |
| Library / Project | Open questions | `open-questions.md` | `current` claims with zero inbound links — the unconnected synthesis backlog. |
| Library / Project | Contradictions | `contradictions.md` | `current` claims carrying a `links.contradicts` note link — open tensions. |
| Project | Project gate | `project-gate.md` | Active Project notes, output mode, active thesis, refutation stamp, and the latest structural-impact cache timestamp/state. |
| Studio | Studio gate | `studio.md` | Synthesis landing surface: `research-focus.md`, claims by maturity, and the pattern library. Project-gate state lives in `project-gate.md`. |
| Maintenance | Drift watch | `drift-watch.md` | Open `flag`/`alert` cards in `proposed` — active/imminent structural drift; HIGH/`alert` findings also surface in the daily glance. |
| Maintenance | Loose ends | `loose-ends.md` | Notice-loudness `flag` cards in `proposed` — low-stakes structural debt batched for the weekly pass. |
| Maintenance | Weekly review | `weekly-review.md` | The Friday aggregator (multi-section). |
| Agent-ops | Audit log | `audit-log.md` | `system/logs/audit.jsonl`, current week; unhandled denies → flag. |
| Agent-ops | Fleet health | `fleet-health.md` | Per-lane trust score / operational rollup from `system/metrics/`. |
| Agent-ops | Eval trend | `eval-trend.md` | Quarterly vault-eval capability scores (recall@k, support-rate, FAMA-clean) from `system/metrics/eval/runs.jsonl` — diagnostic, never gating. |
| Agent-ops | Skill lifecycle | `skill-lifecycle.md` | Which skills are active in which lane, read live from `.memoria/lane-overrides/` + `.memoria/profiles/*/skills/`; mismatches surface as consistency-check rows ([ADR-43](../adr/43-skill-governance.md)). |

The **Surface** column is where a dashboard opens in the UI. The explanation site groups the same twelve by the *kind of attention* they demand — **Home glance → Daily glance**, **Library → Synthesis agenda**, **Maintenance → Structural health**, **Agent-ops → Operational health** ([Dashboards](../explanation/dashboards/README.md)). The two are the same four buckets under different lenses, not different inventories.

---

## The Bases views

Obsidian Bases (`.base` files) are the database views the dashboards and workspaces lean on ([ADR-49](../adr/49-catalog-in-bases-linter-monitor.md)). Bases are views; the notes are the source of truth.

| Base | Lives at | View over |
| --- | --- | --- |
| `catalog.base` | `catalog/` | The Catalog — entity records by type (papers, people, organizations, venues, datasets, repositories), `lifecycle != archived`. |
| `inbox.base` | `inbox/` | The Inbox board — cards grouped by type; "Needs me" = `proposed`; `action`/`finding` columns expose the next thing to decide; converges to empty. |
| `claims.base` | `system/dashboards/` | Claims by maturity. |
| `sources.base` | `system/dashboards/` | Source notes by lifecycle. |
| `fleeting.base` | `system/dashboards/` | Fleeting notes awaiting promote-or-discard. |
| `project-gate.base` | `system/dashboards/` | Project notes by output mode, refutation stamp, maturity, saturation, and cache timestamp. |
| `patterns.base` | `system/patterns/` | The pattern library by mode and lifecycle. |
| `worklists.base` | `system/worklists/` | Batch screening rows grouped by worklist, decision, or group; rows are `worklist-item` notes and one aggregate Inbox prompt points here. |

---

## Verdict band (drift-watch)

The drift-watch dashboard rolls the Linter operation's detector findings up into a `PASS` / `REVIEW` / `FAIL` band; the rollup rule and the severity scale it reads are owned by [Linter: detectors and auto-fix](linter.md#the-detectors).

## Trust score (fleet-health)

A 0–100 composite per lane, computed by `src/.memoria/mcp/metrics_aggregate.py` into `system/metrics/`. Inputs: audit deny rate, structural-drift incidents, secret-field access attempts, retry rate, success rate, and accept/reject ratios on lanes producing proposals. The shipped `fleet-health.md` dashboard embeds a Dataview table over those `lane-metric` notes and shows PI attention fields (`time_on_gate_min`, `expand_then_accept_min`, `card_open_resolve_min`) plus blind re-review sample counts. Bands: **90+ healthy · 70–89 watch · < 70 act**. Suggestion-ratio extremes both down-weight: accept > ~90% = rubber-stamping; < ~20% = candidate scoring needs tuning.

## Eval metrics (eval-trend)

Per-quarter capability scores, computed by the deterministic scorer `src/.memoria/operations/telemetry/eval/eval_score.py` into `system/metrics/eval/runs.jsonl` ([ADR-11](../adr/11-vault-eval-maintenance.md)). Each metric is 0–1, higher is better: **recall@k** (gold citekeys in the top-k retrieved), **support-rate** (cited evidence resolving to real catalog records), **FAMA-clean** (no superseded/archived claim reused). A gold task whose card reported no machine-readable result shows as **unscored** — never a faked score. Diagnostic, not gating: a dip informs the PI; it does not pause scheduled work. Full contract: [Vault eval](vault-eval.md).

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
