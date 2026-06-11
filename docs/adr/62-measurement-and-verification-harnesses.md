---
topic: decisions
id: 62
title: Measurement and verification harnesses
status: deferred
nav_exclude: true
date_proposed: 2026-06-11
date_resolved:
assumes: [11, 20]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 62
---

# ADR-62: Measurement and verification harnesses

## Context

A set of analysis capabilities would make the Verifier measurable, the claim layer richer, and the system's health visible over time. The **minimal capture** they all read — the six-signal operational log (state-transition timestamps + decision time, cost per card, deny reasons, suggestion disposition, FAMA exposure) — is **already decided and shipping**: it is the single highest-leverage action from the publication-path report, emitted and self-tested in v0.1, with schemas pinned in [Telemetry & logs](../reference/telemetry.md) (see [ADR-20 publication path](20-publication-path.md)). Capture cannot be back-filled, so it ships first; the analysis harnesses that read it are deferred because v0.1 has not tripped their adoption conditions. This ADR records only those deferred harnesses.

## Decision

Memoria treats the following analysis harnesses as the approved direction, each built later against accumulated telemetry and scheduled per-item when its condition holds:

- **CiteME-style Verifier regression harness.** A private fixture of ~50 (excerpt → target-claim-note) pairs built from approved vault drafts, scored against the Verifier nightly, with accuracy recorded in a metric note. A Verifier prompt change ships only when fixture accuracy is at or above the running 90th-percentile baseline — preventing silent regression from model updates, context-length changes, or template edits.
- **Chain-of-Evidence claim taxonomy.** Type each substantive claim and require a type-appropriate evidence chain — `citation` (resolved citekey + claim note), `numerical` (the passage containing the figure), `methodological` (protocol summary), `conclusion` (the claim notes it rests on). Adapted from ScientistOne (Meng et al. 2026). The CiteME harness is the gate: adopt typing only if the harness shows it measurably reduces false-clean verdicts. Score verification and method–code alignment are out of scope for knowledge work (Coder lane only).
- **Fleet observability aggregator.** A scheduled aggregator reads the audit log and board history to materialize the [fleet-health dashboard](../explanation/dashboards/operational-health/fleet-health.md) — per-lane and per-skill cost, success rate, retry rate, and latency on daily/weekly/monthly cadence. Until the aggregator exists, the dashboard is empty.
- **Propagation debts re-eval queue.** When a high-traffic note changes (claim promoted to `evergreen`, reference updated, paper retracted), enumerate the dependents needing re-evaluation and record them as a readable queue in the Linter's report. The human works the queue; the agent never rewrites dependents.
- **LLM-judge `prose-check` export gate.** At export time only, a `prose-check` command scores the manuscript on a small fixed rubric (argument coherence, voice consistency, citation grounding) and attaches a report to the export card. It never auto-edits, never blocks export, and never runs against synthesis — the human reads it and decides whether to revise.
- **Execution-trace reflection on retry.** On a retry, a reflection skill reads the failure trace (tool called, arguments, error) and produces a *modified* handoff payload for the next attempt — not an identical redispatch. The reflection layer rewrites the handoff payload for one card only; it never rewrites prompts, skills, or system contracts. A `reflection_count` field (distinct from retry count) shows when reflection itself is exhausted.

## Consequences

- Each harness reads the already-shipping six-signal capture, so the deferral is a scheduling question, not a data-availability one once the log accumulates.
- Several harnesses gate one another (the CiteME fixture gates the claim taxonomy; fleet observability surfaces the retry rate that gates reflection-on-retry), so order matters and the conditions encode it.
- Partial adoption can be worse than none — a claim taxonomy with most claims untyped makes type-aware checks unreliable; a too-small or too-easy CiteME fixture gives false confidence — so each waits for its condition.
- Verdicts stay diagnostic, not gating, consistent with [ADR-11](11-vault-eval-maintenance.md): an eval or prose-check dip informs the human and never auto-halts scheduled work.
- New machinery is required where noted (a scheduled aggregator, structured failure traces in the Kanban dispatcher, fixture-construction effort) — real implementation costs that the conditions defer until justified.

## When this matters

Per-item conditions that raise priority at the cadence review:

- **CiteME regression harness** — the Verifier is live against real drafts *and* at least one project has produced ≥ 20 approved drafts citing ≥ 20 approved claim notes. (Building before the Verifier's behavior settles pins the fixture to a transient prompt.)
- **Chain-of-Evidence taxonomy** — the CiteME harness is live with a measured untyped baseline *and* false-clean Verifier verdicts are a recurring issue; adopt only if the harness shows typing measurably reduces them.
- **Fleet observability aggregator** — at least one of: > 50 tasks/week, multiple scheduled lanes running in parallel, or API spend ≥ $50/month.
- **Propagation debts queue** — the corpus passes ~500 claim notes *and* the human notices, while reading a draft, that a cited claim has shifted.
- **LLM-judge `prose-check` gate** — a deliverable has been re-exported more than twice for issues a model could have caught on the first read.
- **Reflection-on-retry** — sustained retry rate > 0.10 across a lane visible in fleet observability, *or* a specific skill's retry rate crosses 0.20.

## Related

- **Related decisions / Depends on:** [ADR-11 vault-eval as a maintenance capability](11-vault-eval-maintenance.md) (the diagnostic-not-gating discipline and the eval surface these harnesses report through); [ADR-20 publication path](20-publication-path.md) (the six-signal capture these harnesses read, already adopted); [ADR-41 configurable review-gate mode](41-configurable-review-gate-mode.md) (the export/review gate the `prose-check` capability attaches to).
- **Source discussion:** [Telemetry & logs](../reference/telemetry.md).
