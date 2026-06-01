---
topic: proposals
id: PROP-02
title: Cross-run skill-insights memory
status: deferred
created: 2026-05-15
---

# PROP-02: Cross-run skill-insights memory

## What

A `00-meta/skill-insights/` log where Hermes records patterns learned across projects — e.g. "X classifier underperforms when Y" — and surfaces them in future planning sessions. The MetaClaw / CORAL pattern from autonomous-research systems (MetaClaw: multi-round claim extraction that iteratively refines what counts as a learnable signal; CORAL: cross-run aggregation that pools those signals across separate project runs into a queryable log).

## Why

Today Hermes treats every project as fresh — there is no compounding learning across projects. Patterns the human notices stay in their head or in ad-hoc notes, never in a queryable log the agent can reuse.

## Trade-offs

- A real meta-claims schema, a write discipline, and a review surface — all non-trivial to design and maintain.
- Low payoff until the corpus is dense enough that cross-project patterns actually recur and become visible.

## Adoption trigger

A concrete cross-project pattern recurs often enough to be worth capturing — ideally scoped narrowly first (e.g. classifier mis-firings only) rather than a general meta-memory.

## Guard

Do not build the general meta-memory pre-emptively: the architectural overhead is significant and the corpus density that makes such patterns visible does not yet exist. A single-user vault rarely justifies it.

## Alternatives considered

**Adopt now (general).** Rejected: too much architecture for a single-user vault at current density.

**Adopt scoped to a single domain** (e.g. classifier mis-firings). A possible compromise; defer until a concrete recurring pattern justifies even the scoped version.

## Related

- **Files:** none currently.
