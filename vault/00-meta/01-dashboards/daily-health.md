# Daily Health

Open every morning, glance ~30 seconds, close if nothing's red. The **system-health** view — board queues, drift, lane health, cron. Vault-state work (classification debt, promotion queue, orphans) lives in [[weekly-review|Weekly Review]]. [Dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/daily-glance/daily-health/).

## 1. Today's queue

Cards needing you: `blocked` (your decision) or a `done` card with `review_status: requested` (awaiting approval). Oldest first; ≥ 3 rows is the signal to clear them before larger work.

```dataviewjs
const cards = await dv.io.load("99-system/logs/board-state.jsonl");
if (!cards || !cards.trim()) { dv.paragraph("_No data yet._"); return; }
const events = cards.trim().split("\n").filter(Boolean).map(l => JSON.parse(l));
const active = events.filter(e =>
  e.state === "blocked" || e.review_status === "requested"
).sort((a, b) => a.last_updated.localeCompare(b.last_updated)).slice(0, 10);
dv.table(
  ["State", "Lane", "Card", "Waiting since", "Reason"],
  active.map(c => [c.state, c.lane, c.task_id, c.last_updated, c.reason ?? c.review_owner ?? ""])
);
```

## 2. Drift signals

HIGH/CRITICAL structural-detector findings in the last 24h — these pause scheduled work (verdict `FAIL`). If anything appears, treat the day as diagnostic. Full view: [[drift-watch|Drift watch]].

```dataviewjs
const text = await dv.io.load("99-system/logs/lint-findings.jsonl");
if (!text || !text.trim()) { dv.paragraph("_No data yet._"); return; }
const events = text.trim().split("\n").filter(Boolean).map(l => JSON.parse(l));
const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
const high = events.filter(e =>
  e.reported_at >= cutoff && (e.severity === "HIGH" || e.severity === "CRITICAL")
);
dv.table(
  ["Detector", "Severity", "Finding", "Path"],
  high.map(e => [e.detector, e.severity, e.finding, e.path])
);
```

## 3. Lane health

Per-lane trust score. Bands: **90+** healthy · **70–89** watch · **<70** act (pause scheduled work). Empty = the aggregator hasn't run today. Contributing inputs: [[fleet-health|Fleet Health]].

```dataview
TABLE WITHOUT ID
  lane AS Lane,
  trust_score AS Trust,
  task_count AS Tasks,
  task_success_rate AS "Success%"
FROM "99-system/metrics"
WHERE type = "lane-metric" AND period = string(date(today))
SORT trust_score ASC
```

## 4. Cron status

Last/next run for the four standard tasks (`nightly-hygiene`, `weekly-cluster-report`, `weekly-drift-report`, `fleeting-staleness-report`). A missing row = cron not enabled for that lane; ✗ = last run failed.

```dataviewjs
const text = await dv.io.load("99-system/logs/cron-history.jsonl");
if (!text || !text.trim()) { dv.paragraph("_No data yet._"); return; }
const events = text.trim().split("\n").filter(Boolean).map(l => JSON.parse(l));
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

## Related

Queries stay empty until the board-state / lint-findings / metrics / cron-history feeds are wired ([rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/daily-glance/daily-health/)). Siblings: [[weekly-review|Weekly Review]] (Friday vault-state), [[drift-watch|Drift watch]] (structural detail), [[fleet-health|Fleet Health]] (cost & trust inputs), [[audit-log|Audit log]] (forensics).
