---
topic: proposals
id: PROP-NN  # next available PROP number; a separate sequence from ADR ids
title: <short phrase, e.g. "Cross-run skill-insights memory">
status: deferred  # deferred | under-consideration | adopted | rejected
created: YYYY-MM-DD
---

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

## Dependencies

What must be in place first. Other proposals, corpus density, profile wiring.
