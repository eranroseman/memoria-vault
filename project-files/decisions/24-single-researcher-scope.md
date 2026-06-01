---
topic: decisions
id: 24
title: Single-researcher scope — multi-user semantics are out of scope
status: accepted
date_proposed: 2026-06-01
date_resolved: 2026-06-01
supersedes: []
superseded_by: []
---

# ADR-24: Single-researcher scope — multi-user semantics are out of scope

## Context

Memoria assumes one human who owns judgment: review decisions, synthesis choices, and scope priorities all belong to that single researcher. This assumption is stated in [what-memoria-is.md](../../docs/explanation/overview/what-memoria-is.md) but was never recorded as a decision — and unrecorded scope *constraints* are the ones that erode silently, because each individual "could we also support two reviewers / a shared queue / per-user permissions?" looks harmless in isolation. Recording the boundary makes the cumulative cost of crossing it explicit: multi-user review is not a feature increment, it is a different system.

## Decision

Memoria is a knowledge-production system for a **single researcher**. The design assumes exactly one human reviewer who owns all judgment about what enters the canonical vault. **Multi-user review semantics — concurrent reviewers, per-user permissions, shared review queues, attribution/merge of competing judgments — are explicitly out of scope.** Features that assume a single owner of judgment (the blocking review gate of [ADR-03](03-structural-review-gate.md), agent-proposed/human-confirmed classification of [ADR-15](15-project-auto-classification.md), the single declared authority for frontmatter) are correct as designed and are not to be generalized to teams. This is a scope boundary, not a capability claim.

## Consequences

- The review gate stays simple: one reviewer, one verdict, no reconciliation of competing human judgments. This is a feature, not a limitation, at the target scale.
- *Multi-machine* is not *multi-user*: one researcher operating Memoria across several machines is in scope (session files are named to avoid sync collisions — [ADR-25](25-session-logging-two-logs.md)); several humans sharing one vault is not. The distinction is owner-of-judgment count, not device count.
- Any proposal that introduces a second judgment-owner must be treated as superseding this ADR, not extending the current design — it would touch the gate, the audit model, classification confirmation, and permissions at once.
- Team-tool framing is off the table for v0.x, which keeps the novelty surface and the publication path ([ADR-20](20-publication-path.md)) honestly scoped to n=1 operator data.

## Alternatives considered

**Design for teams from the start.** Rejected: multi-user review semantics (concurrency, per-user permissions, merge of competing verdicts) are a different and substantially larger system, and building for them now would complicate the single-owner gate that is central to the design — paying a large cost for a use case the project does not target.

**Leave scope implicit.** Rejected: an unstated boundary gets crossed incrementally. Recording it gives reviewers a single place to point when a feature quietly assumes a second human.

## Related

- **Supporting rationale:** [what-memoria-is.md](../../docs/explanation/overview/what-memoria-is.md) ("single researcher" and "not a team tool in its current form").
- **Related decisions:** [ADR-03 structural review gate](03-structural-review-gate.md) (assumes one reviewer); [ADR-15 project auto-classification](15-project-auto-classification.md) (one human confirms); [ADR-20 publication path](20-publication-path.md) (n=1 operator data accepted as a known weakness).
- **Proposals bounded by this ADR:** [multi-vault-and-multi-machine.md](../proposals/multi-vault-and-multi-machine.md) (cross-machine for one researcher is in scope; a shared multi-user memory server is not, absent a superseding decision).
- **Source discussion:** retroactively records the scope boundary already stated in `what-memoria-is.md`.
