---
title: "Pattern provenance: borrow, adapt, ignore"
parent: Evidence base
grand_parent: Design rationale
nav_order: 2
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

The lookup table is [Pattern provenance table](../../../reference/evidence-and-integrations/pattern-provenance.md).
The public evidence base is the cited [Bibliography](../../../reference/evidence-and-integrations/bibliography.md)
plus that table; the working review covered ~47 systems inside a wider
~400-paper corpus.

## What the survey changes

The useful patterns are structural: stage gates, explicit roles, typed handoffs,
persistent graphs, durable state, and reviewable artifacts. The refused patterns
are mostly scalar-optimization loops: autonomous keep/revert, tournament
evolution, confidence-routed gate bypass, and learned reviewer preferences.

That distinction is the design line. Memoria borrows mechanics that make work
traceable and strips loops that would let the system decide what becomes
canonical.

## Why these patterns are refused

The source examples below preserve the context for each refusal. A useful
mechanic in one of these systems does not make its operating posture compatible
with Memoria's review gate.

| Refused pattern | Representative sources | Why it is refused |
| --- | --- | --- |
| Full autonomous scientist mode | [AI Scientist v2](../../../reference/evidence-and-integrations/bibliography.md#yamada2025aiscientistv2), Sibyl, AI-Researcher, Auto-Research | Runs end-to-end without Memoria's structural gate. |
| Tree search over synthesis | [AIDE ML](../../../reference/evidence-and-integrations/bibliography.md#aideml), AI Scientist v2 | Requires a fixed scalar metric; synthesis quality is not scalar. |
| Autonomous keep/revert | Karpathy Autoresearch | The three safe-loop preconditions fail for knowledge work. |
| Co-trained generator + reviewer | [CycleResearcher](../../../reference/evidence-and-integrations/bibliography.md#weng2025cycleresearcher) | The reviewer's learned preferences become the objective. |
| Tournament/evolution loop | [AI co-scientist](../../../reference/evidence-and-integrations/bibliography.md#gottweis2025aicoscientist) | Sound memory architecture, refused autonomy posture. |
| Preferences internalized into weights | [NanoResearch](../../../reference/evidence-and-integrations/bibliography.md#xu2026nanoresearch) | Preferences stop being inspectable, auditable, or revertible. |
| Confidence-routed gate bypass | AutoResearchClaw SmartPause | Turns a structural gate into a probabilistic one. |
| Harness without a gate | [Sibyl-AutoResearch](../../../reference/evidence-and-integrations/bibliography.md#wang2026sibyl) | Harness rhetoric does not imply human control. |
| Conversation as durable substrate | [AutoGen](../../../reference/evidence-and-integrations/bibliography.md#wu2023autogen) | Conversation is ephemeral; the vault is memory. |
| Generalist sandboxed dev worker | [OpenHands](../../../reference/evidence-and-integrations/bibliography.md#wang2025openhands) | Permission model is too coarse for per-zone, per-profile policy. |

For the factual roster of borrowed, adapted, referenced, and refused patterns,
see the [Pattern provenance table](../../../reference/evidence-and-integrations/pattern-provenance.md).

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

- Lookup table: [Pattern provenance table](../../../reference/evidence-and-integrations/pattern-provenance.md)
- Where the corpus pushes back on these bets: [Literature pushback](literature-pushback.md)
- The principles this survey operationalizes: [Design principles](../foundations/design-principles.md)
- What Memoria is, in system terms: [What Memoria is](../foundations/what-memoria-is.md)
