---
title: Consequence propagation
parent: Knowledge
grand_parent: Explanation
nav_order: 7
---

# Consequence propagation

> **Planned (G4/G5, alpha.22/B1):** Typed graph propagation and eager write-time marking described below are target-state.

Memoria's central operation is what happens *after* a change to the knowledge
base. Any change or addition — a new claim, an edited note, a new or changed
edge, a retracted source, a claim the researcher decides is wrong — has
consequences for everything grounded on it, and the graph's job is to make
those consequences visible instead of letting them rot silently.

## Typed blast radius

Because the graph carries [Toulmin roles](../rationale/foundations/intellectual-foundations.md),
the consequences are *typed*, not generic. When a node falls, its dependents
experience different events:

- **Grounds lost** — a claim's evidence went away; the claim stands unsupported.
- **Warrant lost** — the inference license connecting evidence to claim fell;
  every argument that license covered is affected at once.
- **Qualifier-bounded regression** — a hedged claim degrades only within its
  stated bounds.
- **Rebuttal strengthened** — a counter-argument gains force when its target
  weakens.

A graph that only stores "claim links to claim" cannot distinguish these; one
that stores the roles can route each dependent to the right disposition.

## Consequences are marked at write time

Derivation happens on write: the moment a change lands, its blast radius is
computed and affected nodes are marked — stale, under-warranted, needing
re-confirmation — so the knowledge base is always current and the researcher
gets immediate feedback. Reads may come weeks later; even hours of staleness
can mislead. Re-confirmation of impacted nodes is then *lazy and
impact-ranked*: marking is eager, re-verification effort follows the
researcher's attention to what matters.

## Origin-blind, authority-gated

Epistemic consequences are origin-blind: the blast radius of a wrong claim is
identical whether a human or a machine authored it. Write and revert
*authority* stays origin-gated — human-authored text is never auto-destroyed;
machine material can auto-revert. See
[Design principles](../rationale/foundations/design-principles.md), principles 11–12.

## Related

- [Intellectual foundations](../rationale/foundations/intellectual-foundations.md) — the Toulmin pillar.
- [Knowledge cycle](knowledge-cycle.md) — where propagation sits in the daily loop.
- [Promotion and the write boundary](promotion-and-gated-zones.md) — states, not places.
