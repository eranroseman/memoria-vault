---
topic: decisions
id: 34
title: Code-artifact autopilot
status: rejected
assumes: []
date_proposed: 2026-05-15
date_resolved: 2026-06-16
supersedes: []
superseded_by: []
---

# ADR-34: Code-artifact autopilot

> **Rejected 2026-06-16.** The proposed scheduled-script autopilot is
> structurally precluded by [ADR-21](21-l3-autonomy-ceiling.md)'s L3 autonomy
> ceiling. Code-lane execution remains human-bounded; future work belongs to the
> explicit keep/revert experiment loop tracked in #369, not a per-note unattended
> script flag.

## What

An opt-in `autopilot: true` flag on a `code-note` that lets Hermes run a scripted analysis on a schedule — e.g. a weekly metric-refresh script that regenerates dashboards without a human kickoff. Per-`code-note`, never global.

## Why

Recurring analyses currently need a manual trigger every time. For a genuinely repetitive script with a fixed, scalar output, that kickoff is pure friction the system could absorb.

## Trade-offs

- Scheduled execution means compute spend without a human in the loop — bounded only if a per-run budget and a tight opt-in scope are enforced.
- A failed scheduled run can leave stale metric data downstream; autopilot needs a fail-loud path, not silent staleness.
- Adds a card/note field and dispatch wiring for scheduled code runs.

## Rejection rationale

Memoria will not adopt this shape. A per-`code-note` `autopilot: true` flag creates
unattended code execution from vault content, adds a second execution trigger, and
weakens the L3 ceiling. If repeated code experimentation becomes valuable, it must
use the lane-bounded keep/revert experiment loop: explicit metric, budget, output
path, audit trail, and human promotion.

## Alternatives considered

**Adopt now with a global flag.** Rejected: no current use case warrants the safety overhead.

**Adopt only via the Coder profile's cron, not a per-`code-note` flag.** A possible future shape; defer the choice between the two until a concrete first use case exists.

## Related

- **Tracking issue:** [#369](https://github.com/eranroseman/memoria-vault/issues/369)
  tracks the replacement code-experiment loop shape.
- **Workflows:** [Code](../how-to-guides/project/create-a-code-artifact.md)
- **Files:** [The Coder](../explanation/profiles/engineer.md), `99-system/templates/code-note.md`
- **Related proposal:** [Nightly discovery loop](61-nightly-discovery-loop.md) §2 (Coder experiment loop) — the keep/revert variant of the same Coder-lane autonomy; this proposal is the *scheduled-script* variant.
- **Bounded by:** [ADR-21 L3 autonomy ceiling](21-l3-autonomy-ceiling.md) (the Coder exception).
