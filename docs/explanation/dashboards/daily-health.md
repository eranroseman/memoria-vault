---
topic: dashboards
---

# Daily Health — design summary

**Runtime artifact.** Ships at `00-meta/01-dashboards/index.md` in the [starter vault](https://github.com/eranroseman/memoria-vault) and runs in Obsidian via Dataview; the runtime queries live there. This summary covers the design role.

## Mission

The always-on **system-health** view, opened every morning. Four sections, each one a one-decision query: today's `blocked` cards and those awaiting review (`review_status: requested`), last 24h HIGH/CRITICAL drift signals, lane-health trust scores, and cron status. Glance for 30 seconds. If nothing is red, close it and move on. If something is red, the flagged item names what needs attention before any larger operation.

## What this dashboard is not

- **Not a vault audit.** Folder counts, orphan notes, stale literature — those are the [`weekly-review`](weekly-review.md)'s Friday ritual job. Daily Health is system health, not knowledge health.
- **Not a task list.** It shows decisions waiting on the human; the human chooses which to address. The board, not this dashboard, is where state changes happen.
- **Not a substitute for [`drift-watch`](drift-watch.md), [`fleet-health`](fleet-health.md), or [`audit-log`](audit-log.md).** Daily Health summarizes the *red signals* from each; the full views live in the deeper dashboards. See ["dashboard-of-dashboards" pattern](#dashboard-of-dashboards-pattern) below.

## Design decisions

- **Cron status is unique to Daily Health.** No other dashboard shows cron run history; this is the one section without a deeper counterpart.
- **30-second budget.** The four sections are designed so a healthy day reads as four empty tables and closes. Anything non-empty is a signal to act on or click through to the deeper view.
- **Graceful degradation.** Until the metrics aggregator, the board's markdown card files, the lint-findings JSONL feed, and the cron-history JSONL feed exist, the four queries return empty. The placeholders state what would populate them, so an empty result is interpretable as "feature not yet wired" rather than "nothing wrong" — see [obsidian-ui/dashboards.md graceful-degradation discipline](../../reference/obsidian-ui/dashboards.md#graceful-degradation).

### Dashboard-of-dashboards pattern

Three of the four Daily Health sections are *filtered subsets* of deeper dashboards: drift signals filter [`drift-watch`](drift-watch.md) to last 24h HIGH/CRITICAL; lane health filters [`fleet-health`](fleet-health.md) to lane + trust + tasks + success%; today's queue filters [`board-state`](board-state.md) to `blocked` / awaiting-review (`review_status: requested`). Same data sources, narrower projections. No divergence risk between layers because both read the same underlying note and JSONL files.

Daily Health is the entry point; the deeper dashboards are reached by clicking through. This is what "dashboard of dashboards" means structurally — Daily Health doesn't have its own data, it summarizes red signals from the dashboards that do.

## The full catalog

Daily Health is one dashboard among eleven. The [dashboards index](README.md) lists them all — role, when to open, what each reads from, and closest sibling.

## Related

- [`weekly-review`](weekly-review.md) — Friday-ritual vault-state view
- [`drift-watch`](drift-watch.md) — full structural-detector view + verdict band
- [`fleet-health`](fleet-health.md) — trust score contributing inputs + cost trends
- [`audit-log`](audit-log.md) — per-decision forensics when something needs investigation
- [`board-state`](board-state.md) — full Kanban board view
