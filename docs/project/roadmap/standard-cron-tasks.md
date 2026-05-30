---
topic: roadmap
---

# Standard cron tasks

Memoria ships with four standard scheduled tasks. Each is declared in the relevant profile's `cron/` folder (see [architecture/on-disk-layout.md](../../explanation/architecture/on-disk-layout.md)) and dispatched by the Hermes Kanban according to the schedule. All four are **read-mostly or write-to-logs only** — they produce reports the human reads on a cadence, not edits the human has to review per-task.

```yaml
cron:
  - schedule: "0 2 * * *"          # nightly 02:00
    skill: hygiene-sweep
    lane: linter
    creates_card: {task: nightly-hygiene, state: ready}

  - schedule: "0 3 * * MON"        # weekly Monday 03:00
    skill: cluster-mapping-scan
    lane: mapping
    creates_card: {task: weekly-cluster-report, state: ready}

  - schedule: "0 4 * * MON"        # weekly Monday 04:00
    skill: drift-detector
    lane: linter
    creates_card: {task: weekly-drift-report, state: ready}

  - schedule: "0 5 * * *"          # nightly 05:00
    skill: stale-fleeting-check
    lane: linter
    creates_card: {task: fleeting-staleness-report, state: ready}
```

Three of the four are on the Linter lane (read-only writes go to `00-meta/02-logs/` and dashboard updates) and one is on the Mapper lane (writes a corpus-wide cluster scan to project-scratch). None can modify canonical content — that constraint is what makes scheduled automation safe to enable.

## `cron_mode` migration

Two knobs are easy to conflate. **Whether a cron task is scheduled at all** is a per-job decision — you create the Hermes cron job for a lane. **`approvals.cron_mode`** (default `deny`) is separate: it governs what a cron job does when it hits a command that would normally need human approval — `deny` blocks that command (the agent must find another path), `approve` auto-approves everything in cron context. Cron jobs still *run* under `deny`; they just can't execute dangerous, approval-gated commands unattended. Memoria keeps the `deny` default and schedules cron jobs cautiously, lane by lane, in the order below.

The recommended enablement order, by safety:

1. **Linter first.** All Linter writes go to `00-meta/02-logs/` (audit and session logs) or dashboard files. No content edits, no review-gated-zone writes. Lowest blast radius. Enable after Phase 3 (profile build) is stable.
2. **Mapping next.** Writes go to project-scratch (`40-workbench/*/01-map/corpus-map.md` etc.). No review-gated-zone writes. Enable a few weeks after Linter cron is stable.
3. **Librarian (eventually).** Librarian writes to `10-inbox/` and `20-sources/` — actual content, but in zones the human classifies before promotion. Higher blast radius; enable only after the discovery-loop practice is established (see [future-directions.md — discovery loop](future-directions.md#the-discovery-loop)).
4. **Never auto-enable Writer, Verifier, or Coder.** These produce review-gated artifacts the human must look at; scheduled cron-dispatch would silently fill the review queue. Always human-initiated.
5. **Socratic doesn't apply.** Socratic is `routing.invocation: interactive_only` — the Kanban dispatcher won't queue-dispatch it regardless of `cron_mode`.

The convention: each cron-enable is a deliberate decision recorded in the human's deployment notes. "Linter cron enabled 2026-06-12 after 4 weeks of stable dry-run reports" is the kind of provenance that makes the system auditable when something goes wrong.
