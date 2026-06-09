---
topic: proposals
title: Dashboards — eleven views, four groups, two data sources
status: as-built
created: 2026-06-09
---

# Dashboards — eleven views, four groups, two data sources

A design capture of the eleven dashboards as built: what each shows, where it reads
from, and how they group by the question they answer. Reconstructed from
[`vault/00-meta/01-dashboards/`](../../../vault/00-meta/01-dashboards/) and the
explanation site's grouping.

> **Why capture this.** Eleven Dataview/Dataviewjs dashboards are live, but the only
> exploration touching them was the Fleet-observability item in
> [measurement-and-verification.md](measurement-and-verification.md). This is the
> design view of the full set.

## What it is

Eleven Obsidian dashboards, each a query over either note frontmatter (Dataview) or a
JSONL log (Dataviewjs). They are the system's read-side: where the human and the
agents *see* state, as opposed to the board where work *moves*. They group by reading
moment:

| Group | Dashboards | The question |
|---|---|---|
| **Daily glance** | `daily-health`, `board-state` | "Is anything wrong right now?" |
| **Synthesis agenda** | `reading-pipeline`, `discuss-queue`, `open-questions`, `contradictions` | "What should I read, discuss, or reconcile?" |
| **Structural health** | `drift-watch`, `loose-ends`, `weekly-review` | "What's decaying? (the Friday ritual)" |
| **Operational health** | `fleet-health`, `audit-log` | "How is the agent fleet performing?" |

This grouping matches [`docs/explanation/dashboards/README.md`](../../../docs/explanation/dashboards/README.md).

## How it works

### The eleven views

| Dashboard | Shows | Source |
|---|---|---|
| `daily-health` | board queues, drift signals, lane trust, cron status | board export + `lint-findings.jsonl` + metrics + `cron-history.jsonl` |
| `board-state` | full Kanban: active cards, review queue, retry watch, claim-maturity histogram | board markdown export (`99-system/board/`) |
| `weekly-review` | inbox queue, classification debt, promotion queue, stale literature, orphans | Dataview over `10-inbox/`, `20-sources/`, `30-synthesis/` |
| `contradictions` | claim pairs linked by human-set `relations.contradicts` | Dataviewjs over `30-synthesis/01-claims/` |
| `discuss-queue` | classified papers (`lifecycle: current`) not yet Discussed | Dataview over `20-sources/01-papers/` |
| `reading-pipeline` | papers in flight (`lifecycle: proposed`) + claims by maturity | Dataview over papers + claims |
| `open-questions` | every note carrying an "Open questions" section | Dataview content scan |
| `drift-watch` | Linter findings + verdict band by period + recurring offenders + schema backlog | `lint-findings.jsonl` + metrics |
| `fleet-health` | per-lane trust score (0–100) + cost/reliability trend | `99-system/metrics/lane-metric-*` |
| `loose-ends` | junk filenames + unfinished notes (cleanup signal if > 5) | Dataview over whole vault |
| `audit-log` | policy-MCP decisions: denies, dry-runs, review-gated writes, per-profile 24h, hash drift | `99-system/logs/audit.jsonl` |

### Two data sources

Dashboards read from exactly two kinds of source — that is the design constraint:

1. **Note frontmatter**, via Dataview — the live vault state (lifecycle, maturity,
   relations, type). These work today.
2. **JSONL logs / metrics**, via Dataviewjs — `audit.jsonl`, `lint-findings.jsonl`,
   `cron-history.jsonl`, and the `metrics_aggregate.py` output.

The field-level coupling is itself linted: `detectors.py`'s `dashboard_field_drift`
fails if any dashboard query references a field no template defines (it caught
`review_status`→`status`, `project`→`projects`, `enrichment_updated`→`enriched_date`
during QA). The dashboards can't silently rot against the schema.

### Dependencies (not-yet-built inputs)

Several views stay empty until their feed is wired: `board-state` and the board
sections of `daily-health` need the `99-system/board/` export; `fleet-health`,
`drift-watch`'s verdict band, and the lane/cron sections of `daily-health` need
`metrics_aggregate.py` running end-to-end into `99-system/metrics/`. The queries are
authored; the feeds are the gating work.

## Design rationale

- **Browse views, not an action queue.** Dashboards are for *seeing*; the Inbox/board
  is for *doing*. Splitting them keeps each honest — a dashboard never accumulates
  obligations, and the board never becomes a report.
- **Group by reading moment.** The human looks at different things at session start
  (is anything broken?), mid-research (what do I read?), on Fridays (what's decaying?),
  and when auditing the fleet. The four groups map to those moments rather than to
  data type.
- **Two sources, by constraint.** Restricting dashboards to frontmatter + JSONL keeps
  them declarative and lintable; an arbitrary data source would escape
  `dashboard_field_drift` and rot silently.
- **Single-accent discipline carries over.** Like the callouts, dashboards avoid
  rainbow signaling — urgency comes from queue depth and verdict bands, not color.

## Related

- [session-logging-and-audit.md](session-logging-and-audit.md) — the JSONL feeds and trust score
- [structural-linter-and-drift.md](structural-linter-and-drift.md) — `drift-watch` / `loose-ends` findings
- [ADR-09](../../adr/09-contradictions-dashboard.md) (contradictions), [ADR-13](../../adr/13-homepage-front-door.md) (home front-door)
- Explanation: [`docs/explanation/dashboards/`](../../../docs/explanation/dashboards/); Reference: [`docs/reference/dashboards.md`](../../../docs/reference/dashboards.md)
