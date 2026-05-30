---
topic: dashboards
---

# Dashboards

Dashboards are Dataview queries rendered as notes — the **dashboard** component from [obsidian-ui/README.md](../obsidian-ui/README.md). Each one answers a single recurring question (what's blocked, what's drifting, what's ready to read) and is meant to be opened, glanced at, and closed. This folder holds one design summary per dashboard — each following the shared [design-summary page template](../../reference/templates/design-summary-template.md) — while the runtime Dataview queries ship at `00-meta/01-dashboards/` in the [starter vault](https://github.com/eranroseman/memoria-vault).

[`daily-health`](daily-health.md) is the entry point — opened every morning, it summarizes the red signals from the deeper dashboards and is the page you click through from. (It ships as `00-meta/01-dashboards/index.md` in the starter vault.) For the design rules every dashboard follows (one decision per query, filter the boring cases, sort oldest-first) and the Dataview performance discipline, see [obsidian-ui/dashboards.md](../../reference/obsidian-ui/dashboards.md).

## All dashboards at a glance

The dashboards fall into an entry glance (Daily Health), operational and structural health (audit-log, board-state, drift-watch, fleet-health), knowledge and reading (open-questions, contradictions, discuss-queue, reading-pipeline), maintenance (loose-ends, and the *deferred* skill-lifecycle), and the weekly ritual that orchestrates them. Ten dashboards plus the `index.md` entry point ship in the starter vault; `skill-lifecycle` is deferred (see [implementation-status.md](../../project/implementation-status.md)). The order below follows that grouping; each row's last column is the one comparison worth keeping straight.

| Dashboard | Role | When to open | Reads from | Closest sibling |
|---|---|---|---|---|
| [`daily-health`](daily-health.md) | system-health glance | every morning, 30s | red signals from the three deeper health dashboards (drift-watch, fleet-health, board-state), plus cron | entry point for all below |
| [`audit-log`](audit-log.md) | per-write forensics | a write looks wrong; after an overnight run | `audit.jsonl` | [`drift-watch`](drift-watch.md) — per lint pass, not per write |
| [`board-state`](board-state.md) | workflow execution | reviewing cards from inside Obsidian | `00-meta/board/` markdown cards | [`discuss-queue`](discuss-queue.md) — cards, not content |
| [`drift-watch`](drift-watch.md) | structural drift | the system feels wrong; after profile/plugin changes | `lint-findings.jsonl` | [`audit-log`](audit-log.md); [`fleet-health`](fleet-health.md) |
| [`fleet-health`](fleet-health.md) | operational health | the fleet runs real weekly volume (Phase 6+) | `lane-metric` / `skill-metric` notes | [`drift-watch`](drift-watch.md) — structural counterpart |
| [`open-questions`](open-questions.md) | research agenda | planning the next research direction | claim + paper notes with `# Open questions` | — (works day one) |
| [`contradictions`](contradictions.md) | claim-tension surfacing | building an argument; weekly synthesis | claim notes with `relations.contradicts` | [`open-questions`](open-questions.md) — agenda from tensions, not questions |
| [`discuss-queue`](discuss-queue.md) | upstream discipline | sitting down to read | paper notes `lifecycle: current`, no `processed:` | [`reading-pipeline`](reading-pipeline.md) — broader |
| [`reading-pipeline`](reading-pipeline.md) | upstream flow | the inbox feels full | paper notes `lifecycle: proposed` + claim maturity | [`discuss-queue`](discuss-queue.md) — narrower |
| [`loose-ends`](loose-ends.md) | naming hygiene | after ingest batches | filename keywords, whole vault | Linter `orphan-working-files` — automation, not human |
| [`skill-lifecycle`](skill-lifecycle.md) *(deferred)* | skill governance | adding or auditing skills, once stood up | `skill-note` files | — |
| [`weekly-review`](weekly-review.md) | knowledge ritual | Friday, ~90 min | orchestrates the dashboards above | [`daily-health`](daily-health.md) — weekly, not daily |
