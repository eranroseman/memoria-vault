---
title: Dashboards
parent: Reference
---

# Dashboards

The primary dashboards are the three durable space notes under `spaces/`
(`src/spaces`): Library, Knowledge, and Project. The Inbox queue (`spaces/inbox.md`,
`type: queue`) and Maintenance collection (`spaces/maintenance.md`, `type: maintenance`)
sit alongside them by cadence: daily action vs weekly structural debt. Both are reached
from the navigation rail's **Now**. Supporting dashboards and Bases live under
`system/dashboards/` (`src/system/dashboards`) and related data folders. Space
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
| Queue | Inbox | `spaces/inbox.md` | Action-first triage queue (`type: queue`), reached from the rail's *Now*: the Inbox `Needs me` and fleeting-note processing views. |
| Maintenance | Maintenance | `spaces/maintenance.md` | Weekly structural-debt collection (`type: maintenance`): drift-watch, loose-ends, and board views. |
| Space | Library | `spaces/library.md` | Source intake space: reading pipeline, discuss queue, and Catalog papers. |
| Space | Knowledge | `spaces/knowledge.md` | Synthesis space: claims by maturity, open questions, contradictions, hubs, and patterns. |
| Space | Project | `spaces/project.md` | Project steering space: active projects, saturation, and project gaps. |
| Maintenance support | Board state | `system/dashboards/board-state.md` | The full Inbox board (embeds `inbox.base` — "Needs me" = cards in `proposed`, with the card's `action`/`finding` visible) plus live worker cards from `system/board/`. |
| Library support | Reading pipeline | `system/dashboards/reading-pipeline.md` | Object-first Bases view: source notes at `lifecycle: proposed` awaiting reading & distillation + current claims by maturity. |
| Library support | Discuss queue | `system/dashboards/discuss-queue.md` | Source notes at `lifecycle: provisional` — read but not yet distilled; worth a Co-PI pass. |
| Knowledge support | Open questions | `system/dashboards/open-questions.md` | `current` claims with zero inbound links — the unconnected synthesis backlog. |
| Knowledge support | Contradictions | `system/dashboards/contradictions.md` | `current` claims carrying a `links.contradicts` note link — open tensions. |
| Project support | Project gate | `system/dashboards/project-gate.md` | Active Project notes, output mode, active thesis, refutation stamp, and the latest structural-impact cache timestamp/state. |
| Maintenance | Drift watch | `system/dashboards/drift-watch.md` | Open `flag`/`alert` cards in `proposed` — active/imminent structural drift; these count in the rail health band. |
| Maintenance | Loose ends | `system/dashboards/loose-ends.md` | Notice-loudness `flag` cards in `proposed` — low-stakes structural debt batched for the weekly pass. |
| Maintenance | Weekly review | `system/dashboards/weekly-review.md` | The Friday aggregator (multi-section). |
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
| `inbox.base` | `inbox/` | The Inbox board — cards grouped by type; "Needs me" = `proposed`; `action`/`finding` columns expose the next thing to decide; converges to empty. |
| `board.base` | `system/board/` | Live worker cards by lane/state, mirrored from Hermes board state. |
| `claims.base` | `system/dashboards/` | Claims by maturity. |
| `sources.base` | `system/dashboards/` | Source notes by lifecycle. |
| `fleeting.base` | `system/dashboards/` | Fleeting notes awaiting promote-or-discard. |
| `project-gate.base` | `system/dashboards/` | Project notes by output mode, refutation stamp, maturity, saturation, and cache timestamp. |
| `hubs.base` | `notes/hubs/` | Hub notes by topic cluster and lifecycle. |
| `projects.base` | `projects/` | Project notes by output mode, thesis state, saturation, and open gaps. |
| `patterns.base` | `system/patterns/` | The pattern library by mode and lifecycle. |
| `worklists.base` | `system/worklists/` | Batch screening rows grouped by worklist, decision, or group; rows are `worklist-item` notes and one aggregate Inbox prompt points here. |

### Verified Bases behavior

The supported dashboard UI relies on these Obsidian 1.12.7 Bases behaviors:

- Wikilinks inside nested `links:` maps register as backlinks, so typed edges such
  as `links.contradicts` are visible both to contradiction views and to orphan
  checks that use `file.backlinks`.
- Native Bases filters handle nested relation presence checks such as
  `!links.contradicts.isEmpty()`; no materialized `has_contradiction` field is
  needed for the shipped contradiction view.
- Warm-cache Bases rendering is not the current scale limit: a 7,004-row grouped
  view with multi-key sort and formulas rendered in about 1.4 seconds in the
  sandbox.
- Cold metadata parsing is the scale risk: a 10,000-file bulk write took about
  76 seconds before the metadata cache fully settled. Future projection work must
  wait for cache settlement before signalling readiness; see
  [ADR-102](../adr/102-disposable-projection-engine.md).

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

For the exact `lane-metric` fields and trust-score calculation, see [Fleet metrics](fleet-metrics.md) and [Telemetry log schemas](telemetry-logs.md).

## Related

- The detectors behind drift-watch: [Linter: detectors and auto-fix](linter.md)
- The audit-log schema fleet-health and audit-log read: [Memory substrates](memory.md)
- The card types the Inbox board groups: [Note types](note-types.md)
- Where the dashboards open by default: [Obsidian workspaces](obsidian-workspaces.md)
