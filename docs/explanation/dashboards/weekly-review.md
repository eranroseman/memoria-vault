---
topic: dashboards
---

# `weekly-review` — design summary

**Runtime artifact.** Ships at `00-meta/01-dashboards/weekly-review.md` in the [starter vault](https://github.com/eranroseman/memoria-vault) and runs in Obsidian via Dataview; the runtime queries live there. This page covers the design role.

## Mission

The Friday-ritual entry point. Open at the start of each weekly session and work top-to-bottom: clear the inbox, decide candidates, promote `evergreen` claim notes, check orphans, review project pages, glance at metrics. The discipline is **one ritual per week, ~90 minutes top-to-bottom** — not "open whenever." A scheduled weekly cadence is what keeps the vault from accumulating drift faster than it produces synthesis.

## What this dashboard is not

- **Not [Daily Health](daily-health.md).** Daily Health is the daily glance (open every morning, 30 seconds). Weekly is knowledge ritual (open Friday afternoon, 90 minutes). Different rhythm, different scope.
- **Not the only weekly view.** [`reading-pipeline`](reading-pipeline.md), [`loose-ends`](loose-ends.md), and [`drift-watch`](drift-watch.md) are also "weekly" by recommended cadence — but weekly-review is the ritual *entry point* that links to them and orchestrates the order.
- **Not auto-actioned.** Every section requires human decisions (promote / archive / discard / triage). Nothing in this dashboard happens by cron.

## Design decisions

- **Top-to-bottom ordering matches the workflow.** Inbox review → discovery candidates → promotion queue → orphan check → project pages → metrics. The order isn't arbitrary: clearing the inbox unblocks downstream synthesis; promotion comes before metrics because the metrics reflect promotion behavior.
- **Empty-section discipline.** A healthy week leaves several sections empty. Empty isn't a bug; it's the goal for sections like "Notes older than 7 days unreviewed."
- **The orphan check carries a coverage@k angle.** Beyond the raw orphan count (notes with zero inlinks), surface *qualifying notes not yet linked or found* — claims or papers that should connect to current work but don't (KnowledgeBerg; AutoResearchBench Wide-Research). This catches missing *coverage*, not just disconnected notes. See [roadmap/evaluation.md](../../project/roadmap/evaluation.md) (Observability).
- **Schema-version migration progress is intentionally NOT here.** That belongs in [`drift-watch`](drift-watch.md)'s schema-migration-progress section — the weekly-review surfaces *content decisions*, not *structural maintenance*. Mixing the two crowds the human's Friday attention.
- **Discovery candidates section degrades gracefully.** Until [ADR-21 shared candidate frontmatter](../../project/decisions/21-shared-candidate-frontmatter.md) is adopted and a `candidate-note` template exists, that section is empty by design.

## Related

- [`reading-pipeline`](reading-pipeline.md) — papers-by-stage view; linked from weekly-review for reading planning
- [`loose-ends`](loose-ends.md) — leftover-junk surfacer; weekly companion
- [`drift-watch`](drift-watch.md) — structural drift findings (also weekly)
- [workflows/maintenance/lint.md](../../how-to/workflows/maintenance/lint.md) — the weekly ritual the dashboard structures
