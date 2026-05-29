# Daily Health — always-on health monitor

**Location.** `00-meta/01-dashboards/index.md`

**Decision.** Open every morning. Glance for 30 seconds. If nothing is red, close it and move on. If something is red, the surfaced item tells you what needs attention before any larger operation.

**What this is not.** The vault-state queries (unreviewed synthesis, classification debt, evergreen promotion queue, orphan notes) live in [`weekly-review.md`](weekly-review.md) — those belong in the Friday ritual, not the daily glance. This dashboard is the **system-health** view: board queues, drift signals, lane health, cron status. Four sections, each one a one-decision query.

## 1. Today's queue

Cards demanding your attention — `status: blocked` for explicit human decisions, `review_status: requested` (a `done` card) for agent-completed work awaiting approval. Oldest first; cap at ten so the dashboard doesn't grow unbounded.

```dataviewjs
const cards = await dv.io.load("00-meta/02-logs/board-state.jsonl");
const events = cards.trim().split("\n").map(l => JSON.parse(l));
const active = events.filter(e =>
  e.state === "blocked" || e.review_status === "requested"
).sort((a, b) => a.last_updated.localeCompare(b.last_updated)).slice(0, 10);
dv.table(
  ["State", "Lane", "Card", "Waiting since", "Reason"],
  active.map(c => [c.state, c.lane, c.task_id, c.last_updated, c.reason ?? c.review_owner ?? ""])
);
```

Empty result is the goal. Three or more rows is the signal to clear them before starting larger work.

## 2. Drift signals

Findings from the Linter's eight structural detectors in the last 24 hours, severity HIGH or CRITICAL only. Anything that lands here pauses scheduled work — that's what the verdict band's `FAIL` state means. See [`drift-watch.md`](drift-watch.md) for the full structural-detector view; this section is just the alarm.

```dataviewjs
const text = await dv.io.load("00-meta/02-logs/lint-findings.jsonl");
const events = text.trim().split("\n").map(l => JSON.parse(l));
const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
const high = events.filter(e =>
  e.reported_at >= cutoff && (e.severity === "HIGH" || e.severity === "CRITICAL")
);
dv.table(
  ["Detector", "Severity", "Finding", "Path"],
  high.map(e => [e.detector, e.severity, e.finding, e.path])
);
```

Empty is the goal. If anything appears here, treat the day as a diagnostic day — the architecture is reporting an integrity issue, not a workflow issue.

## 3. Lane health

The [fleet-health dashboard](fleet-health.md)'s trust score per lane, summarized. Bands: 90+ healthy (no action), 70–89 watch (something is slipping), <70 act (pause scheduled work).

```dataview
TABLE WITHOUT ID
  lane AS Lane,
  trust_score AS Trust,
  task_count AS Tasks,
  task_success_rate AS "Success%"
FROM "00-meta/08-metrics"
WHERE type = "lane-metric" AND period = string(date(today))
SORT trust_score ASC
```

Any lane at <70 is a flag. Click through to [`fleet-health.md`](fleet-health.md) for the contributing inputs (audit deny rate, drift incidents, retry rate, accept/reject ratios). If the trust score is empty entirely, the aggregator hasn't run today yet (cron failure or recent vault open).

## 4. Cron status

Last run and next run for the four standard cron tasks (see [standard cron tasks](../../../memoria-docs/roadmap/standard-cron-tasks.md)). A missed nightly run is a signal — the system didn't sweep, drift may have accumulated, scheduled cards aren't in the queue.

```dataviewjs
const text = await dv.io.load("00-meta/02-logs/cron-history.jsonl");
const events = text.trim().split("\n").map(l => JSON.parse(l));
const byTask = {};
for (const e of events) {
  if (!byTask[e.task] || e.completed_at > byTask[e.task].completed_at) {
    byTask[e.task] = e;
  }
}
const rows = Object.entries(byTask).map(([task, e]) => [
  task, e.lane, e.completed_at, e.next_scheduled, e.exit_code === 0 ? "✓" : "✗"
]);
dv.table(["Task", "Lane", "Last run", "Next run", "Result"], rows);
```

All four standard tasks should appear: `nightly-hygiene` (Linter), `weekly-cluster-report` (Mapping), `weekly-drift-report` (Linter), `fleeting-staleness-report` (Linter). A missing row means cron isn't enabled for that lane (see the [`cron_mode` migration](../../../memoria-docs/roadmap/standard-cron-tasks.md#cron_mode-migration)); a row with ✗ in Result means the last run failed.

## Graceful degradation

Until the metrics aggregator, board-state JSONL feed, and lint-findings JSONL feed exist, the four queries above return empty. The placeholders state what would populate them, so an empty result is interpretable as "feature not yet wired" rather than "nothing wrong."

- `00-meta/02-logs/board-state.jsonl` — written by the Kanban dispatcher when cards transition states.
- `00-meta/02-logs/lint-findings.jsonl` — written by the Linter on each pass.
- `00-meta/08-metrics/lane-metric-*` — written by the scheduled metrics aggregator (see [`fleet-health.md`](fleet-health.md)).
- `00-meta/02-logs/cron-history.jsonl` — written by Hermes after each cron task completes.

## Related

- [`weekly-review.md`](weekly-review.md) — Friday-ritual vault-state view (top-to-bottom in 90 minutes).
- [`drift-watch.md`](drift-watch.md) — full structural-detector view + verdict band.
- [`fleet-health.md`](fleet-health.md) — trust score contributing inputs + cost trends.
- [`audit-log.md`](audit-log.md) — per-decision forensics when something needs investigation.
