---
topic: decisions
id: 35
title: Cross-run skill-insights memory
status: accepted
assumes: []
date_proposed: 2026-05-15
date_resolved: 2026-06-19
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 35
---

# ADR-35: Cross-run skill-insights memory

## What

A `00-meta/skill-insights/` log where Hermes records patterns learned across projects — e.g. "X classifier underperforms when Y" — and surfaces them in future planning sessions. The MetaClaw / CORAL pattern from autonomous-research systems (MetaClaw: multi-round claim extraction that iteratively refines what counts as a learnable signal; CORAL: cross-run aggregation that pools those signals across separate project runs into a queryable log).

## Why

Today Hermes treats every project as fresh — there is no compounding learning across projects. Patterns the human notices stay in their head or in ad-hoc notes, never in a queryable log the agent can reuse.

## Trade-offs

- A real meta-claims schema, a write discipline, and a review surface — all non-trivial to design and maintain.
- Low payoff until the corpus is dense enough that cross-project patterns actually recur and become visible.

## When this matters

A concrete cross-project pattern recurs often enough to be worth capturing — ideally scoped narrowly first (e.g. classifier mis-firings only) rather than a general meta-memory. The detection prerequisite **now exists**: alpha.5 added the classify-miss instrumentation, so a recurrence sweep over the logs can surface "trigger ready" instead of relying on the operator noticing — the narrow slice (sweep → Inbox card → `skill-insights/`) is buildable now; only the *volume* of recurrences is usage-gated.


## Alternatives considered

**Adopt now (general).** Rejected: too much architecture for a single-user vault at current density.

**Adopt scoped to a single domain** (e.g. classifier mis-firings). Accepted as the prudent first implementation shape once the linked issue is ready.

## Related

- **Tracking issue:** [#371](https://github.com/eranroseman/memoria-vault/issues/371) — implementation readiness lives on the issue.
- **Files:** none currently.
