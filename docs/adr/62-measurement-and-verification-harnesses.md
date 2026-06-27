---
topic: decisions
id: 62
title: Measurement and verification harnesses
nav_exclude: true
status: accepted
date_proposed: 2026-06-11
date_resolved: 2026-06-16
assumes: [11, 20]
supersedes: []
superseded_by: []
---

# ADR-62: Measurement and verification harnesses

## Context

A set of analysis capabilities would make the Peer-reviewer measurable, the claim layer richer, and the system's health visible over time. The **minimal capture** they all read — the six-signal operational log (state-transition timestamps + decision time, cost per card, deny reasons, suggestion disposition, FAMA exposure) — is the single highest-leverage action from the publication-path report, with schemas pinned in [Telemetry & logs](../reference/telemetry.md) (see [ADR-20 publication path](20-publication-path.md)). Capture cannot be back-filled, so the schema and available emitters ship first. ADR-106 closed the former card-overlay gap by joining cost to Hermes session rows and writing disposition at the human review action. This ADR records the harness family: the fleet observability aggregator has shipped, while the remaining harnesses stay deferred until their per-item conditions raise priority.

## Decision

Memoria treats the following analysis harnesses as the approved direction:

- **CiteME-style Peer-reviewer regression harness.** A private fixture of ~50 (excerpt → target-claim-note) pairs built from approved vault drafts, scored against the Peer-reviewer nightly, with accuracy recorded in a metric note. A Peer-reviewer prompt change ships only when fixture accuracy is at or above the running 90th-percentile baseline — preventing silent regression from model updates, context-length changes, or template edits.
- **Chain-of-Evidence claim taxonomy.** Type each substantive claim and require a type-appropriate evidence chain — `citation` (resolved citekey + claim note), `numerical` (the passage containing the figure), `methodological` (protocol summary), `conclusion` (the claim notes it rests on). Adapted from ScientistOne (Meng et al. 2026). The CiteME harness is the gate: adopt typing only if the harness shows it measurably reduces false-clean verdicts. Score verification and method–code alignment are out of scope for knowledge work (code lane only).
- **Fleet observability aggregator.** A scheduled aggregator reads the audit log and board history to materialize the [fleet-health dashboard](../explanation/dashboards/operational-health/fleet-health.md) — per-lane and per-skill cost, success rate, retry rate, and latency on daily/weekly/monthly cadence. This slice is built as `metrics_aggregate.py` and the `memoria-metrics` cron wrapper.
- **Propagation debts re-eval queue.** When a high-traffic note changes (claim promoted to `evergreen`, reference updated, paper retracted), enumerate the dependents needing re-evaluation and record them as a readable queue in the Linter's report. The human works the queue; the agent never rewrites dependents.
- **LLM-judge `prose-check` export gate.** At export time only, a `prose-check` command scores the manuscript on a small fixed rubric (argument coherence, voice consistency, citation grounding) and attaches a report to the export card. It never auto-edits, never blocks export, and never runs against synthesis — the human reads it and decides whether to revise.
- **Execution-trace reflection on retry.** On a retry, a reflection skill reads the failure trace (tool called, arguments, error) and produces a *modified* handoff payload for the next attempt — not an identical redispatch. The reflection layer rewrites the handoff payload for one card only; it never rewrites prompts, skills, or system contracts. A `reflection_count` field (distinct from retry count) shows when reflection itself is exhausted.

## Consequences

- Each remaining deferred harness reads the six-signal capture model. Cost and disposition now have first-class emitters through the [ADR-106](106-cost-and-disposition-capture.md) path; `cost-misses.jsonl` rows are data-quality misses, not zero-cost activity.
- Several harnesses gate one another (the CiteME fixture gates the claim taxonomy; fleet observability surfaces the retry rate that gates reflection-on-retry), so order matters and the conditions encode it.
- Partial adoption can be worse than none — a claim taxonomy with most claims untyped makes type-aware checks unreliable; a too-small or too-easy CiteME fixture gives false confidence — so each waits for its condition.
- Verdicts stay diagnostic, not gating, consistent with [ADR-11](11-vault-eval-maintenance.md): an eval or prose-check dip informs the human and never auto-halts scheduled work.
- New machinery is still required where noted (structured failure traces in the Kanban dispatcher, fixture-construction effort, export-time prose check) — real implementation costs that the conditions defer until justified.

## When this matters

Per-item conditions that raise priority at the cadence review:

- **CiteME regression harness** — the Peer-reviewer is live against real drafts *and* at least one project has produced ≥ 20 approved drafts citing ≥ 20 approved claim notes. (Building before the Peer-reviewer's behavior settles pins the fixture to a transient prompt.)
- **Chain-of-Evidence taxonomy** — the CiteME harness is live with a measured untyped baseline *and* false-clean Peer-reviewer verdicts are a recurring issue; adopt only if the harness shows typing measurably reduces them.
- **Fleet observability aggregator** — built in v0.1.0-alpha.4 as `metrics_aggregate.py` plus the `memoria-metrics` cron wrapper.
- **Propagation debts queue** — the corpus passes ~500 claim notes *and* the human notices, while reading a draft, that a cited claim has shifted.
- **LLM-judge `prose-check` gate** — a deliverable has been re-exported more than twice for issues a model could have caught on the first read.
- **Reflection-on-retry** — sustained retry rate > 0.10 across a lane visible in fleet observability, *or* a specific skill's retry rate crosses 0.20.

## Current implementation mapping

The telemetry schema and downstream aggregation contract are current system behavior.
`audit.jsonl`, `board-state.jsonl`, `board-transitions.jsonl`,
`lint-findings.jsonl`, `disposition.jsonl`, and `cost.jsonl` emit through their
documented writers. ADR-106 deliberately keeps cost and disposition off the card
metadata overlay: cost/tokens join a completed card to the Hermes session store via
`hermes kanban show <id> --json` and
`runs[].metadata.worker_session_id`, while disposition is written by the
`Memoria: resolve inbox card` QuickAdd action. Consumers must treat
`cost-misses.jsonl` rows as join-quality misses, never as valid zero-cost runs.

## Related

- **Related decisions / Depends on:** [ADR-11 vault-eval as a maintenance capability](11-vault-eval-maintenance.md) (the diagnostic-not-gating discipline and the eval surface these harnesses report through); [ADR-20 publication path](20-publication-path.md) (the six-signal capture these harnesses read, already adopted); [ADR-41 configurable review-gate mode](41-configurable-review-gate-mode.md) (the export/review gate the `prose-check` capability attaches to).
- **Source discussion:** [Telemetry & logs](../reference/telemetry.md).
- **Tracking issues:** [#412](https://github.com/eranroseman/memoria-vault/issues/412)
  — cadence review for the harness family;
  [#737](https://github.com/eranroseman/memoria-vault/issues/737) — implemented
  session-store/review-action path for `disposition.jsonl` and `cost.jsonl`.
