---
title: "Pattern provenance: borrow, adapt, ignore"
parent: Design Book
grand_parent: Developers
nav_order: 30
---

# Pattern provenance: borrow, adapt, ignore

Pattern provenance records where each design pattern came from and what Memoria
did with it: borrowed, adapted, used only as framing, or refused.

The distinction matters because many autonomous-scientist systems pair useful
mechanics with an autonomy posture Memoria rejects. Provenance keeps those
separate: a reader can see whether a pattern was omitted by ignorance or by
judgment.

Memoria uses four verdicts:

- **Borrow** — adopted as-is; the mechanic solved a real problem and needed no
  change.
- **Adapt** — the mechanic is kept, but the autonomy posture is narrowed.
- **Reference** — useful framing, without a borrowable pattern.
- **Ignore** — evaluated and explicitly refused.

The lookup table is [Pattern provenance table](../reference/pattern-provenance.md).
The evidence base is a ~47-system survey inside a wider ~400-paper review
(`_papers/`, verdicts in `_papers/REVIEW-SUMMARY.md`).

## What the survey changes

The useful patterns are structural: stage gates, explicit roles, typed handoffs,
persistent graphs, durable state, and reviewable artifacts. The refused patterns
are mostly scalar-optimization loops: autonomous keep/revert, tournament
evolution, confidence-routed gate bypass, and learned reviewer preferences.

That distinction is the design line. Memoria borrows mechanics that make work
traceable and strips loops that would let the system decide what becomes
canonical.

## Net effect

The design shift versus a generic "agent-assisted knowledge base" is from
agent-assisted to **bounded, phase-gated knowledge production**:

- Agents become better at bookkeeping, retrieval, and drafting.
- The human remains the gatekeeper for meaning, promotion, and final structure.
- Every scalar-optimization loop that sits on top of a useful mechanic is
  removed.

This makes the architecture easier to debug: each phase has a traceable
responsibility, and nothing reaches checked knowledge without a recorded PI
disposition where one is required.

## Related

- Lookup table: [Pattern provenance table](../reference/pattern-provenance.md)
- Where the corpus pushes back on these bets: [What the literature pushes back on](what-the-literature-pushes-back-on.md)
- The principles this survey operationalizes: [Design principles](design-principles.md)
- What Memoria is, in system terms: [What Memoria is](what-memoria-is.md)
