---
topic: decisions
id: 61
title: Nightly discovery loop, code-experiment loop, and Writer-proposed claims
status: deferred
nav_exclude: true
date_proposed: 2026-06-11
date_resolved:
assumes: [34, 37, 21]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 61
---

# ADR-61: Nightly discovery loop, code-experiment loop, and Writer-proposed claims

## Context

Three related capabilities extend what the agent does *between* human gates without moving the gates themselves: a proactive overnight discovery loop, a keep/revert experiment loop scoped to the code lane, and Writer-proposed candidate claim notes. Each absorbs friction the operator currently bears manually, and each carries a distinct over-automation risk. They are grouped here because they share the same boundary discipline — autonomy expands within the lane, the structural review gate stays put — and because none is gated on a static trigger; the conditions below are cadence-review context.

## Decision

Memoria will, when scheduled, add:

1. **A nightly proactive discovery loop.** Hermes runs unattended on a nightly cron: read `research-focus.md`, pick top N priorities (default 3), run `find` per priority (max 10 candidates each), ingest the previous day's confirmed candidates, enrich stale paper notes, then commit and post a morning summary. This converts discovery from reactive (operator-triggered) to proactive. Silent cron failure is the dominant operational risk — the loop fails loud, never silent.

2. **A code-lane keep/revert experiment loop.** A lane-bounded `code-experiment-loop` skill runs propose → test → keep-if-improved → revert-otherwise for up to N iterations against a pre-defined scalar success criterion. A `code-experiment` card type carries `success_metric:`, `budget_iterations:`, and `budget_cost_usd:` fields. Output lands in `projects/<project>/code/experiments/<run-id>/`; the policy MCP permits writes only to that path. When the budget exhausts, a summary card goes to `done` (`review_status: requested`) with the best variant, its diff, and the metric trajectory for human promotion. Scoped to code (monotonic metric, reversible changes, independent experiments) — explicitly not synthesis.

3. **Writer-proposed candidate claim notes.** After a `discuss` card closes, the Writer proposes *candidate* claim notes from the discussed source as `type: candidate` drafts landing in `inbox/`, each carrying its provenance (source note plus the specific passage). The policy MCP denies writes to `notes/claims/`; the human edits, authors the canonical claim, or discards. Depends on claim-sentence classification and a `candidate` card type on the shared candidate schema (ADR-17).

## Consequences

- The nightly loop requires always-on infrastructure (Syncthing + VPS); a sleep-prone machine misses the cron. Bad inclusion criteria flood the inbox and make morning triage unsustainable.
- The experiment loop optimizes the metric, not the goal: a poorly-specified `success_metric:` produces a winner that game-played the test, and loose budgets balloon API spend.
- Writer-proposed claims are the most judgment-adjacent automation in the roadmap, with two named risks: rubber-stamping (a fluent candidate invites acceptance without close reading) and framing capture (the agent's phrasing anchors the human's). Over-proposing is worse than not proposing.

## When this matters

*(Cadence-review context, not a gate.)*

- **Nightly discovery loop** — all four hold: (1) Memoria v0.1 stable, (2) `research-focus.md` maintained for ≥ 4 weeks, (3) always-on deployment active (Syncthing + VPS), (4) `screening-plan.md` written down. Adopting before inclusion criteria are written floods the inbox and makes triage the slowest part of the day.
- **Code experiment loop** — the operator notices running the same "edit → test → revert if worse" cycle more than ~10–20 times per project, *and* a scalar success criterion existed *before* the cycle started.
- **Writer-proposed claims** — `discuss` and `distill` are stable *and* the felt bottleneck is *transcribing* claims, not comprehending them. Prototype on a handful of sources and measure the accept-unedited rate; a high rate is a warning, not a win. If comprehension is the bottleneck, this does not help.

## Related

- **Related decisions / Depends on:** [ADR-34 code-artifact autopilot](34-code-artifact-autopilot.md) (the *scheduled-script* variant of code-lane autonomy; this is the *keep/revert experiment* variant); [ADR-37 retriever-scout](37-retriever-scout-profile.md) (the discovery/find mechanism the nightly loop drives); [ADR-21 L3 autonomy ceiling](21-l3-autonomy-ceiling.md) (the boundary all three respect, with the retired Coder-lane exception); [ADR-17](17-shared-candidate-frontmatter.md) (the shared candidate schema candidates route on).
- **Tracking issue:** [#411](https://github.com/eranroseman/memoria-vault/issues/411) — revisit at each release cadence.
