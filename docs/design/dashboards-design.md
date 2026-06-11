---
topic: explorations
title: Dashboards — ten views, four groups, two data sources
status: as-built
created: 2026-06-09
parent: Design notes
grand_parent: Explanation
nav_order: 5
---

# Dashboards — ten views, four groups, two data sources

A design capture of the dashboards as shipped in v0.1.1: what each shows, where it
reads from, and how they group by the question they answer. Reconstructed from
[`vault/system/dashboards/`](../../src/system/dashboards), the Bases views, and
[`home.md`](../../src/home.md).

> **Why capture this.** The read-side of the system — where the human *sees* state —
> was only described view-by-view on the explanation site. This is the design view
> of the full set, including what changed from the v0.1.0 eleven-view set.

## What it is

Ten dashboard pages in `system/dashboards/`, a set of Obsidian **Bases** views they
embed ([ADR-49](../adr/49-catalog-in-bases-linter-monitor.md)), and the `home.md`
front door ([ADR-13](../adr/13-homepage-front-door.md)) that carries the above-fold
status glance. Each is a query over either note frontmatter (Dataview / Bases) or a
JSONL log (Dataviewjs). They are the system's read-side: where the human *sees*
state, as opposed to the Inbox/board where work *moves*. They group by reading
moment:

| Group | Views | The question |
|---|---|---|
| **Daily glance** | Home's status glance, `board-state` | "Is anything wrong right now?" |
| **Synthesis agenda** | `reading-pipeline`, `discuss-queue`, `open-questions`, `contradictions` | "What should I read, discuss, or reconcile?" |
| **Structural health** | `drift-watch`, `loose-ends`, `weekly-review` | "What's decaying? (the Friday ritual)" |
| **Operational health** | `fleet-health`, `audit-log` | "How is the agent fleet performing?" |

This grouping matches [`docs/explanation/dashboards/README.md`](../explanation/dashboards/README.md).

Two views from the v0.1.0 eleven changed shape rather than surviving as files:
**`daily-health` was absorbed into `home.md`** (the front door's status glance — one
Dataviewjs block over `board-state.jsonl` + `lint-findings.jsonl`; the file no
longer exists), and **`board-state` became the Inbox board** — a thin page embedding
`inbox.base` plus the live worker cards projected into `system/board/`.

## How it works

### The ten views

| Dashboard | Shows | Source |
|---|---|---|
| `board-state` | the Inbox board (`inbox.base` "Needs me" = cards in `proposed`) + live worker cards | `inbox/` frontmatter + `system/board/` projections |
| `reading-pipeline` | sources awaiting reading/distillation (`lifecycle: proposed`) + claims by maturity | Dataview over `notes/source/` + `notes/claims/`; embeds `claims.base` |
| `discuss-queue` | read-but-not-distilled sources (`lifecycle: provisional`) worth a co-PI pass | Dataview over `notes/source/` |
| `open-questions` | unconnected claims — `lifecycle: current` with zero inlinks (the synthesis backlog) | Dataview over `notes/claims/` |
| `contradictions` | claims carrying a typed `links.contradicts`, unresolved | Dataview over `notes/claims/` ([ADR-09](../adr/09-contradictions-dashboard.md)/[ADR-52](../adr/52-links-vs-relationships.md)) |
| `drift-watch` | open `flag`/`alert` cards in `proposed` (Linter + sweeps findings), by loudness | Dataview over `inbox/` |
| `loose-ends` | Notice-loudness structural debt, batched for the weekly pass | Dataview over `inbox/` |
| `weekly-review` | the Friday aggregator: Notice findings + the week's new catalog/notes movement | Dataview over `inbox/`, `catalog/`, `notes/` |
| `audit-log` | policy-MCP decisions: recent denies/dry-runs, per-profile activity | Dataviewjs over `system/logs/audit.jsonl` (30 s self-refresh) |
| `fleet-health` | **[placeholder]** per-lane trust score + cost/reliability trend | `system/metrics/lane-*` notes — see the deferral note |

### The Bases views

The database layer the dashboards and Home lean on (Bases are views; the notes are
the source of truth):

| Base | Lives at | View over |
|---|---|---|
| `inbox.base` | `inbox/` | the action queue — cards by type; "Needs me" = `proposed` |
| `catalog.base` | `catalog/` | entity records by type, `lifecycle != archived` |
| `claims.base` | `system/dashboards/` | claims by maturity ([ADR-50](../adr/50-universal-lifecycle-and-maturity.md)) + retracted |
| `sources.base` | `system/dashboards/` | source notes by lifecycle (the reading list) |
| `fleeting.base` | `system/dashboards/` | fleeting captures awaiting distill-or-archive |
| `patterns.base` | `system/patterns/` | the pattern library by mode and lifecycle |

### Two data sources

Dashboards read from exactly two kinds of source — that is the design constraint:

1. **Note frontmatter**, via Dataview and Bases — the live vault state (lifecycle,
   maturity, links, type, loudness). These work today.
2. **JSONL logs / metrics**, via Dataviewjs — `audit.jsonl`, `board-state.jsonl`,
   `lint-findings.jsonl`, and the `metrics_aggregate.py` output.

The field-level coupling is itself linted: the Linter engine's
`dashboard_field_drift` detector ([`detectors.py`](../../src/.memoria/engines/linter/detectors.py))
fails if any dashboard query references a field no template defines — the
dashboards can't silently rot against the schema. It runs as a blocking `--gate`
detector in CI.

### Dependencies and deferrals

- **`fleet-health` is a shipped placeholder**: the trust-score queries read the
  `system/metrics/` notes that `metrics_aggregate.py` writes on the installer-wired
  weekly cron (`memoria-metrics`, Mondays 06:30); the page stays a `[placeholder]`
  until real run-volume accrues — trust-score bands are meaningless on sparse data
  ([#205](https://github.com/eranroseman/memoria-vault/issues/205)).
- **`lint-findings.jsonl` has no producer yet** (the Linter engine runs report-only —
  CI, pre-commit, and the daily `memoria-lint` cron all discard or print findings
  rather than appending to the vault log), so Home's findings count and the drift
  sections degrade to their explanatory empty-states.
- **Views don't auto-refresh reliably in Obsidian** — the JSONL views poll every
  30 s as a workaround; the underlying bug is
  [#168](https://github.com/eranroseman/memoria-vault/issues/168).
- **v0.1.2 read-side surfaces** that extend this set: the Bases batch-screening
  worklists for high-cardinality decisions (D37/[ADR-54](../adr/54-two-decision-kinds-batch-worklists.md),
  [#336](https://github.com/eranroseman/memoria-vault/issues/336)) and the
  status-bar ambient indicator (Linter findings + queue counts,
  [#375](https://github.com/eranroseman/memoria-vault/issues/375)).
- **Loudness is display-only for now**: `drift-watch` / `loose-ends` sort and batch
  by the cards' loudness field, but the graded-loudness *routing* — alert/block
  cards pushing to the human instead of waiting to be read — is deferred,
  [#343](https://github.com/eranroseman/memoria-vault/issues/343).

## Design rationale

- **Browse views, not an action queue.** Dashboards are for *seeing*; the Inbox is
  for *doing*. Splitting them keeps each honest — a dashboard never accumulates
  obligations, and the board never becomes a report. (`board-state` embedding
  `inbox.base` doesn't blur this: the Base *is* the queue; the dashboard page just
  frames it.)
- **Group by reading moment.** The human looks at different things at session start
  (is anything broken?), mid-research (what do I read?), on Fridays (what's decaying?),
  and when auditing the fleet. The four groups map to those moments rather than to
  data type.
- **Two sources, by constraint.** Restricting dashboards to frontmatter/Bases + JSONL
  keeps them declarative and lintable; an arbitrary data source would escape
  `dashboard_field_drift` and rot silently.
- **Empty is success.** A healthy vault shows near-empty dashboards; missing feeds
  show explanatory text, never an error — a new vault should not look broken while
  data accumulates.
- **Single-accent discipline carries over.** Like the callouts, dashboards avoid
  rainbow signaling — urgency comes from queue depth, loudness, and verdict bands,
  not color.

## Related

- [Session logging and audit — two logs, tamper-evidence, fleet trust](session-logging-and-audit.md) — the JSONL feeds and trust score
- [Structural linter and drift detection — zero-LLM vault health](structural-linter-and-drift.md) — the findings `drift-watch` / `loose-ends` render
- [ADR-09](../adr/09-contradictions-dashboard.md) (contradictions), [ADR-13](../adr/13-homepage-front-door.md) (home front-door), [ADR-49](../adr/49-catalog-in-bases-linter-monitor.md) (Bases)
- Explanation: [`docs/explanation/dashboards/`](../explanation/dashboards); Reference: [`docs/reference/dashboards.md`](../reference/dashboards.md)
