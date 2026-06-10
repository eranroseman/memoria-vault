---
topic: decisions
id: 34
title: Code-artifact autopilot
status: deferred
assumes: []
date_proposed: 2026-05-15
parent: Decisions
grand_parent: Explanation
nav_order: 34
nav_exclude: true
---

# ADR-34: Code-artifact autopilot

## What

An opt-in `autopilot: true` flag on a `code-note` that lets Hermes run a scripted analysis on a schedule — e.g. a weekly metric-refresh script that regenerates dashboards without a human kickoff. Per-`code-note`, never global.

## Why

Recurring analyses currently need a manual trigger every time. For a genuinely repetitive script with a fixed, scalar output, that kickoff is pure friction the system could absorb.

## Trade-offs

- Scheduled execution means compute spend without a human in the loop — bounded only if a per-run budget and a tight opt-in scope are enforced.
- A failed scheduled run can leave stale metric data downstream; autopilot needs a fail-loud path, not silent staleness.
- Adds a card/note field and dispatch wiring for scheduled code runs.

## When this matters

A specific recurring analysis (e.g. a weekly metric refresh) has been run manually on a regular cadence and the manual kickoff is the felt friction — not a hypothetical "might be useful."

## Alternatives considered

**Adopt now with a global flag.** Rejected: no current use case warrants the safety overhead.

**Adopt only via the Coder profile's cron, not a per-`code-note` flag.** A possible future shape; defer the choice between the two until a concrete first use case exists.

## Related

- **Workflows:** [Code](../how-to-guides/compose/create-a-code-artifact.md)
- **Files:** [The Coder](../explanation/profiles/engineer.md), `99-system/templates/code-note.md`
- **Related proposal:** [Discovery loop and autonomy within the boundary](../design/discovery-loop.md) §2 (Coder experiment loop) — the keep/revert variant of the same Coder-lane autonomy; this proposal is the *scheduled-script* variant.
- **Bounded by:** [ADR-21 L3 autonomy ceiling](21-l3-autonomy-ceiling.md) (the Coder exception).
