---
topic: proposals
id: PROP-NN  # next available PROP number; a separate sequence from ADR ids
title: <short phrase, e.g. "Cross-run skill-insights memory">
status: deferred  # deferred | under-consideration | adopted | rejected
created: YYYY-MM-DD
---

<!--
Section conventions for a single-capability proposal:
  Required     — What, Why, Trade-offs, Adoption trigger, Guard
  Recommended  — Alternatives considered, Related
  Optional     — Dependencies (only when something must be in place first)
A thematic exploration that bundles several capabilities drops `id` from the
frontmatter (keep `title`) and repeats a lighter What / Trade-offs / Adoption
trigger / Guard block per capability instead of these top-level sections.
-->

# [Capability name]

## What

One paragraph: what this adds to the system. Write in the present tense as if it's already built.

## Why

The problem or gap it addresses. What breaks or what's missing without it?

## Trade-offs

What it costs or risks. Be specific — complexity, maintenance burden, permission changes, cost.

## Adoption trigger

The specific condition that would schedule this. Not "when needed" — a concrete, observable signal:
- A specific failure mode that recurs N times
- Corpus reaching a specific size or density
- A concrete project type that demands it
- A measurable quality gap (e.g., Verifier false-negative rate above X%)

## Guard

Why NOT to adopt this early. What goes wrong if adopted before the trigger fires?

## Alternatives considered

The other shapes weighed and why they lost — including "adopt now" and "drop the idea entirely" where they apply. One bold lead-in per alternative.

## Related

Links to the workflows, profiles, files, and decisions this touches. Use `none currently` if there are none.

## Dependencies

*(Optional.)* What must be in place first — other proposals, corpus density, profile wiring.
