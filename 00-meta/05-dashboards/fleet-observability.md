# `fleet-observability.md` — cost and reliability of the worker fleet

**Location.** `00-meta/05-dashboards/fleet-observability.md`

**Decision.** Track whether the Hermes fleet is healthy — cost per task trending up, success rate trending down, retries climbing, latency spikes. This is operations-tier, not architecture-tier: it only matters once the fleet is doing enough work per week that one stuck card or one runaway loop is hard to spot by eye.

**When to enable.** After Phase 6 in [07-roadmap.md](../07-roadmap/future-directions.md). Before then, the volume is low enough that the [board-state dashboard](board-state.md) and the [audit-log dashboard](audit-log.md) catch issues directly.

## Required note types

This dashboard reads two new note types kept in `00-meta/08-metrics/`:

- `lane-metric` — one note per lane per review period (daily / weekly).
- `skill-metric` — one note per skill per review period.

These notes are not in the canonical 15 — they're operational telemetry, not knowledge. They are written by a scheduled Hermes task that aggregates the audit log and the board's task history. Until that task exists, the dashboard is a placeholder.

### Frontmatter shape

```yaml
---
type: lane-metric
lane: research
period: 2026-05-25         # daily or YYYY-WW for weekly
task_count: 128
success_count: 120
incident_count: 2
cost_per_task: 0.12
cost_per_success: 0.15
task_success_rate: 0.94
retry_rate: 0.08
avg_latency_ms: 4200
trust_score: 92            # 0–100; computed by the aggregator from the inputs below
trust_inputs:
  audit_deny_rate: 0.01    # deny + dry_run / total decisions (lower is better)
  drift_incidents: 0       # linter drift reports in the period
  secret_hits: 0           # secret-scanner findings on writes
  retry_rate: 0.08         # mirror of the field above; included so the score is reproducible
  success_rate: 0.94       # mirror; same reason
  suggestion_accept_rate: 0.55   # accepted / total inline [!suggestions] decisions; sweet spot 30–80%
  suggestion_volume: 47          # raw count; large denominators make the ratio meaningful
updated_at: 2026-05-25T23:59:00Z
---
```

The `skill-metric` shape is identical but uses `skill_name` instead of `lane`.

## System trust score

The headline single number — a 0–100 aggregate per lane combining audit cleanliness, drift, secrets, retries, and success. **Read this first.** If trust is dropping, the cost and retry tables below tell you *where*; the [audit-log dashboard](audit-log.md) tells you *why*.

```dataview
TABLE lane AS Lane, trust_score AS Trust, audit_deny_rate AS "Deny%", drift_incidents AS Drift, secret_hits AS Secrets, task_success_rate AS Success
FROM "00-meta/08-metrics"
WHERE type = "lane-metric" AND period = string(date(today))
SORT trust_score ASC
```

Interpretation:

| Score | Posture |
| --- | --- |
| **90–100** | Healthy. Audit clean, no drift, retries within band. No action. |
| **70–89** | Watch. Something is slipping — usually retry rate or audit deny rate climbing. Look at the contributing input on the audit-log dashboard before the score crosses 70. |
| **<70** | Act. At least one input is materially off. A Socratic profile with any allowed write, a Researcher's writes degraded to `dry_run` repeatedly, or a profile-build drift uncaught for a full period all land here. Pause new scheduled work until resolved. |

The score is intentionally a soft aggregate, not a contract. Sustained `<70` means investigate; a transient dip after a known event (a deliberate lane-override change, a one-time migration) is expected and not actionable.

## Fleet summary (current period)

The headline numbers. If the success rate drops by more than 5 percentage points week-over-week, something has regressed.

```dataview
TABLE lane AS Lane, task_count AS Tasks, task_success_rate AS "Success", retry_rate AS Retries, cost_per_task AS "Cost/task", avg_latency_ms AS "Latency (ms)"
FROM "00-meta/08-metrics"
WHERE type = "lane-metric" AND period = string(date(today))
SORT cost_per_task DESC
```

## Cost trend (last 4 weeks)

A growing `cost_per_task` while `task_count` stays flat is the signal of model drift, prompt bloat, or a loop calling tools more than it should.

```dataview
TABLE lane AS Lane, period AS Period, task_count AS Tasks, cost_per_task AS "Cost/task", retry_rate AS Retries
FROM "00-meta/08-metrics"
WHERE type = "lane-metric" AND updated_at > date(today) - dur(28 days)
SORT lane ASC, period ASC
```

## Most expensive skills

Where the spend is actually going. The first row should usually be `paper-lookup` (high call volume) or `generic-rest-bridge` (variable cost per endpoint).

```dataview
TABLE skill_name AS Skill, lane AS Lane, task_count AS Tasks, cost_per_task AS "Cost/task", failure_rate AS Failures
FROM "00-meta/08-metrics"
WHERE type = "skill-metric" AND period = string(date(today))
SORT cost_per_task DESC
LIMIT 10
```

## Retry hotspots

Retries are not free — they cost twice and signal upstream brittleness. A skill or lane with `retry_rate > 0.15` is unhealthy.

```dataview
TABLE lane AS Lane, period AS Period, retry_rate AS "Retry rate", incident_count AS Incidents
FROM "00-meta/08-metrics"
WHERE type = "lane-metric" AND retry_rate > 0.15
SORT retry_rate DESC
```

## Suggestion accept/reject ratios

Inline `[!suggestions]` callouts (see [06-surfaces.md](../06-surfaces/inline.md)) are the most volume-prone agent surface — link candidates, classification proposals, candidate MOC updates. Two failure modes:

- **Rubber-stamping** (`suggestion_accept_rate > 0.90`) — the human is approving without reading. The bounded 5+5 cap and review batching only partly defend against this; the ratio is the canonical signal.
- **Prompt drift** (`suggestion_accept_rate < 0.20`) — the agent is consistently proposing things the human rejects. Time to revisit the producing skill's prompt or threshold.

```dataview
TABLE lane AS Lane, period AS Period, suggestion_volume AS Volume, suggestion_accept_rate AS "Accept%", trust_score AS Trust
FROM "00-meta/08-metrics"
WHERE type = "lane-metric" AND suggestion_volume > 0 AND (suggestion_accept_rate > 0.90 OR suggestion_accept_rate < 0.20)
SORT suggestion_accept_rate DESC
```

The query surfaces only the outliers — sustained healthy lanes (30–80% accept) don't appear. An empty table is the goal.

## Review cadence

A tiered loop, lifted from operational practice in fleet management:

| Cadence | Focus |
| --- | --- |
| **Daily (30 sec)** | Glance at fleet summary. Any incident count > 0? Any lane in `retry hotspots`? |
| **Weekly (5 min)** | Walk the cost trend. Look for week-over-week regression. Check the most-expensive-skills list against the previous week. |
| **Monthly (20 min)** | Compare model mix, prompt revisions, and policy changes against cost movement. Decide what to deprecate. |
| **Quarterly (1 hr)** | Re-evaluate the lane × profile architecture. If a lane is consistently expensive *and* low-success, the contract may need to change. |

A sudden spike in `cost_per_task` without a corresponding spike in `task_count` is almost always a [model-routing drift](../01-architecture/capability-stack.md#model-routing-synthesis-on-claude-cheap-tasks-elsewhere) — a profile that was meant to call a cheap model started falling back to Claude. The fix is in the profile's `config.yaml`, not in the dashboard.

## What this dashboard does not do

- **Not a billing dashboard.** Aggregate cost is reported elsewhere (the Hermes config that emits these notes is also responsible for billing reconciliation).
- **Not a substitute for the audit log.** Per-decision forensics live in the [audit-log dashboard](audit-log.md). This dashboard is the trend view.
- **Not active during MVS.** Until the corpus is large enough that the human eye stops noticing problems, this dashboard is overhead.
