---
topic: decisions
id: 96
title: Code-lane keep/revert experiment loop
nav_exclude: true
status: proposed
date_proposed: 2026-06-19
date_resolved:
assumes: [21]
supersedes: []
superseded_by: []
---

# ADR-96: Code-lane keep/revert experiment loop

## Context

Some coding work follows a repeated edit, test, keep-if-improved, revert-if-worse
cycle. That pattern is safer in code than in synthesis because the work can be
bounded by a scalar success criterion and reversible diffs.

The rejected scheduled-script shape was a per-code-note `autopilot: true` flag. That
would create unattended code execution from vault content, add a second execution
trigger, and weaken the L3 autonomy ceiling. The safer useful core is the explicit
keep/revert loop: metric, budget, output path, audit trail, and human promotion.

## Proposal

Memoria may add a lane-bounded `code-experiment-loop` skill with `success_metric:`,
`budget_iterations:`, and `budget_cost_usd:`. Outputs land under
`projects/<project>/code/experiments/<run-id>/`, and human promotion remains
required.

## Consequences

- Automates repetitive code experiments while keeping the review gate intact.
- Optimizes the metric, not necessarily the goal.
- Requires strict budgets and write-scope enforcement.

## When this matters

The operator repeats the same edit/test/revert cycle more than about 10 to 20
times per project, and a scalar success criterion exists before the loop starts.

## Alternatives considered

**Use ordinary coding agents only.** Simpler, but loses the keep/revert loop's
measurement discipline.

**Per-note scheduled autopilot.** Rejected because it creates unattended code execution
from vault content instead of a lane-bounded, budgeted experiment.

**Apply the loop to synthesis.** Rejected because synthesis lacks a monotonic,
safe scalar metric and reversible success semantics.

## Related

- **Related decisions / Depends on:** [ADR-21](21-l3-autonomy-ceiling.md).
- **Tracking issue:** [#709](https://github.com/eranroseman/memoria-vault/issues/709).
