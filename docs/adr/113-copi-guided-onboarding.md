---
topic: decisions
id: 113
title: "Co-PI-guided onboarding (deferred)"
status: proposed
date_proposed: 2026-06-22
date_resolved:
assumes: [112]
supersedes: []
superseded_by: []
nav_exclude: true
---

# ADR-113: Co-PI-guided onboarding (deferred)

This ADR records a deferred design: letting the **Co-PI run the first loop in
conversation** instead of (or alongside) the doc tutorial that [ADR-112](112-tutorial-destination-first-arc.md)
ships. It is kept `proposed` so the idea is on record with its preconditions, not built.

## Context

ADR-112 delivers onboarding as **doc pages the learner reads while doing**. But Memoria's
entire interface is the **Co-PI** — a conversational agent that already "questions your
thinking, explains the system, and delegates durable work." The AI-native form of
onboarding is therefore not a manual read beside the work; it is the Co-PI *walking the
learner through the first loop in conversation* — driving the palette through
orient → capture → distill → draft → verify → loop → graduate, with the docs as the
reference behind it.

## Decision

*(Proposed — deferred.)* When built, an onboarding skill lets the Co-PI dramatize the
ADR-112 arc conversationally. The **single-script** rule is the crux: the agent and the
docs read from **one** beat definition, so the two representations cannot drift. The
lazy-correct path is incremental — the doc arc (ADR-112) ships first, then the Co-PI
merely *offers* "want me to walk you through your first loop?" against that same script.

## Consequences

- **Pro:** native to the tool, adaptive to the learner, no read-while-do split, higher
  activation than prose.
- **Con:** a real build — an onboarding skill plus the Co-PI driving palette commands —
  and a *second representation of the same flow* that must be held in sync with the docs.
- **Why deferred:** the ADR-112 doc arc is the script the agent layer would dramatize, so
  it must exist and stabilize first; building the agent layer against a moving doc flow
  would mean syncing two moving targets.

## When this matters

Revisit when both hold: (a) the ADR-112 doc arc is implemented and stable, and (b) a
skill/onboarding mechanism exists for the Co-PI to drive palette commands. The
single-script design (docs and agent from one source) is the precondition that keeps the
two from drifting — which is why this `assumes: [112]`: if the doc arc's beats change, this
proposal's script changes with them.

## Alternatives considered

**Build the agent-guided flow now, instead of the doc arc.** Rejected: the doc arc is the
script; authoring the script first is cheaper and is the thing the agent would read.

**Drop agent-guided onboarding entirely.** Rejected: for an agent-centric tool it is the
best-practice end state; keeping it as a deferred ADR preserves the intent without paying
for it before its preconditions are met.

## Related

- **Assumes / dramatizes:** [ADR-112: Onboarding is one destination-first project arc](112-tutorial-destination-first-arc.md).
- **The agent it would drive:** [The Co-PI](../explanation/profiles/co-pi.md).
- **Source discussion:** first-principles design session, 2026-06-22.
