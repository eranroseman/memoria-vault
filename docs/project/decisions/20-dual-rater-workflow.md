---
topic: decisions
id: 20
title: Dual-rater workflow for inter-rater reliability
status: proposed
date_proposed: 2026-05-15
date_resolved:
supersedes: []
superseded_by: []
---

# ADR-20: Dual-rater workflow for inter-rater reliability

## Context

Formal scoping reviews and systematic reviews often require inter-rater reliability calculations ([Cohen's kappa](../../reference/glossary.md#external-tools-and-standards)) on inclusion/exclusion decisions. Adding `rater_1`, `rater_2`, `rater_agreement` fields would support this.

## Decision

**Activate only when the chapter or paper requires reported agreement *and* a second human rater exists.** Resolve disagreements in a reconciliation session and set `rater_agreement: resolved`. (The second-rater precondition matches the activation trigger in the [adopt-on-demand cluster](adopt-on-demand-for-reviews.md#the-members).)

## Consequences

- Solo reading and synthesis ignore the rater fields entirely.
- Formal reviews can report Cohen's kappa on inclusion decisions when the bar requires it.
- Meaningless without a second human rater — adoption requires a collaborator, not just a flag.

## Alternatives considered

**Single-rater always**: See [adopt-on-demand cluster rationale](adopt-on-demand-for-reviews.md).

**Hermes as the second rater**: rejected explicitly — agent judgment doesn't satisfy inter-rater reliability protocols, which exist precisely to triangulate *human* disagreement.

## Related

- **Part of:** [Adopt-on-demand: systematic-review tooling](adopt-on-demand-for-reviews.md) — the shared rationale, plus the other three members (ADR-12, ADR-18, ADR-19).
- **Files affected:** `00-meta/03-templates/paper-note.md` (in the starter vault)
