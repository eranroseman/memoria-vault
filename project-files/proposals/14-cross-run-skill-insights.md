---
topic: proposals
id: 14
title: Cross-run skill-insights memory
status: proposed
date_proposed: 2026-05-15
date_resolved:
supersedes: []
superseded_by: []
---

# ADR-14: Cross-run skill-insights memory

## Context

Have Hermes maintain a `00-meta/skill-insights/` log of patterns learned across projects — e.g., "X classifier underperforms when Y" — surfaced in future planning sessions? This is the MetaClaw / CORAL pattern from autonomous research systems (MetaClaw: multi-round claim extraction framework that iteratively refines what counts as a learnable signal; CORAL: cross-run aggregation and learning pattern that pools those signals across separate project runs into a queryable log).

## Decision

**Defer.** Too much architecture for a single-user vault to justify yet.

## Consequences

- Hermes treats every project as fresh; no compounding learning across projects.
- Patterns the human notices stay in their own head or in ad-hoc notes, not in a queryable log.
- If adopted later, the cost includes a schema, a write discipline, and a review surface — all non-trivial.

## Alternatives considered

**Adopt now**: rejected — the architectural overhead (a meta-claims schema, a write protocol, a review surface) is significant, and the corpus density that makes such cross-project patterns visible doesn't exist yet.

**Adopt scoped to a single domain** (e.g., classifier mis-firings only): a possible compromise. Defer until a concrete recurring pattern justifies even the scoped version.

## Related

- **Files affected:** none currently
