---
title: The Daily Health dashboard
parent: Daily glance
grand_parent: Dashboards
---


# The Daily Health dashboard

Daily Health is the always-on system-health view, opened every morning. It lives at `00-meta/01-dashboards/daily-health.md`. The budget is 30 seconds — glance, decide whether anything is red, close. If nothing is red, move on to real work.

---

## What it shows

Four sections, each a one-decision query: today's **blocked cards and those awaiting review**, the last 24-hour **HIGH/CRITICAL drift signals**, per-lane **trust scores**, and **cron status**. Each is a "is anything red?" check, not a place to do work — the dashboards it summarizes (board-state, drift-watch, fleet-health) are where you act.

---

## What this dashboard is not

**Not a vault audit.** Folder counts, orphan notes, stale literature — those are the weekly-review's job. Daily Health is *system health*, not *knowledge health*. Mixing them would make a 30-second daily glance into a 20-minute triage session.

**Not a task list.** It shows decisions waiting on the human; the human chooses which to address. The board, not this dashboard, is where state changes happen.

**Not a substitute for the deeper dashboards.** Daily Health summarizes red signals; the full views live in `drift-watch`, `fleet-health`, and `audit-log`. It is a dashboard-of-dashboards: three of its four sections are filtered subsets of those deeper views.

---

## Why it's designed this way

**The dashboard-of-dashboards pattern.** Drift signals filter `drift-watch` to last 24 hours HIGH/CRITICAL only. Lane health filters `fleet-health` to current-lane trust scores only. Today's queue filters `board-state` to blocked and awaiting-review only. No data is duplicated; both layers read the same underlying files. Daily Health is the entry point; the deeper dashboards are reached by clicking through.

**Cron status is unique to Daily Health.** No other dashboard shows cron run history. This is the one Daily Health section without a deeper counterpart — it has nowhere else to live. If the overnight lint job didn't fire, the human needs to know before proceeding with the day's work.

**Graceful degradation.** When a feed has no data yet — a fresh vault with no cron runs, no lint findings, or low board volume — the relevant section returns empty with a placeholder stating what would populate it. Empty means "nothing to report," not "something is broken."

**30 seconds is a constraint, not a aspiration.** A daily ritual that consistently takes more than 30 seconds stops being daily. Daily Health is designed so that a healthy vault produces four empty or near-empty sections and the human closes it immediately. Length is a signal: a long Daily Health means something needs attention, not that the ritual needs more time allocated.

---

## Related

- The weekly-ritual companion: [The weekly-review dashboard](../structural-health/weekly-review.md)
- What populates today's queue: [The board-state dashboard](board-state.md)
- What populates the drift signals: `drift-watch`
- What populates the trust scores: `fleet-health`
