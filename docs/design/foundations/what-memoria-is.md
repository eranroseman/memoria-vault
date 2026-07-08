---
title: What Memoria is
parent: Foundations
grand_parent: Design
nav_order: 1
---


# What Memoria is

## The central insight

**Maintaining a knowledge base is a bookkeeping problem, not an intelligence problem.**

Humans are excellent at recognizing what matters and forming original arguments. They are poor at consistently updating summaries, patching broken links, filing useful answers, and running structural health checks. Those tasks are mechanical, repetitive, and easy to defer — and because they're deferred, knowledge bases stagnate. Notes pile up without synthesis; citations go unverified; gaps go unnoticed.

The AI agent is suited for exactly those bookkeeping tasks. Memoria's design follows from this: make the agent narrower and more reliable, and let the human do the irreducibly judgment-laden work. This is not a claim about agent capability — it's a claim about which tasks should be delegated. **Memoria gives the bookkeeping to the agent and keeps judgment human.**

---

## What Memoria is

Memoria is an **opinionated, phase-gated, bounded, personal tool for thinking and writing** — a durable research vault that compounds across months and years.

**Personal** — thinking is private and separate from communication; notes stay unfiltered, preserving raw reasoning before audience-aware editing sanitizes it. The design assumes one human who owns judgment: review decisions, synthesis choices, and scope priorities all belong to that researcher. This is not a team tool.

**Opinionated** — it enforces specific workflows and eliminates setup paralysis. The vault structure, the document types, and the review gates are not configurable surfaces to tune; they are the design.

**Phase-gated** — work passes through defined phases with explicit outputs. A
source doesn't become synthesis until it has been captured, enriched, read, and
compiled; a draft doesn't become a deliverable until it has been verified and
accepted. Worker `checked` state means required checks and warrants passed, not
that the PI approved the claim as true. Each phase has a clear entry and exit
condition.

**Bounded** — agent autonomy is structurally constrained. The agent does not decide what is worth keeping or promote claims to canonical knowledge; the PI does. These limits are structural — enforced by the system's architecture, not by prompt instructions.

It is **knowledge production**, not just storage: the vault grows more useful over time as new sources connect to existing claims, synthesis sharpens as evidence accumulates, and structural maintenance keeps the graph coherent. That is the difference between a research vault and a notes pile.

Day to day, that work happens at three spaces: you bring sources into the **Library**, build them into connected claims in **Knowledge**, and drive an inquiry to output in a **Project**. You act on what the agents surface for you in the **Inbox** queue.

---

## What Memoria is not

**Not an autonomous research scientist.** Contemporary AI research systems (AI Scientist, AI co-scientist, [CORAL](../../reference/bibliography.md#qu2026coral)) run experiments end-to-end, generate papers without review, and promote outputs to canonical based on scalar metrics. Memoria declines this posture for knowledge work — synthesis quality is not scalar, and synthesis errors compound across everything that later cites them.

**Not a general-purpose chat assistant.** Chat history is ephemeral. Conversations are inputs to filing, not the substrate of memory. If a useful answer lives only in a chat transcript, it hasn't been captured.

**Not a Deep Research agent.** Deep Research tools (OpenAI DR, Gemini DR, Perplexity DR) are query-driven and ephemeral: they produce a comprehensive report per query and end. Memoria is corpus-curating and durable: the human builds a vault over months, and each session compounds with prior sessions. The two categories serve different needs.

**Not a single-agent system.** "One model does everything" produces unclear
responsibility, ambiguous permission boundaries, and no separation between
discovery and synthesis. Memoria explicitly avoids this. One read-only Co-PI
posture plus scoped operation postures, each with narrow authority and a clear
exit condition, replace one generalist.

**Not a team tool in its current form.** The design assumes one human reviewer who owns judgment about what enters the canonical vault. Multi-user review semantics are not in scope.

---

## The problem it solves

A research vault typically fails in one of two ways:

1. **Capture without synthesis.** Sources accumulate in the inbox and never move forward. Notes pile up but don't connect. The vault grows but doesn't compound.

2. **Synthesis without rigor.** Bullets replace citations. Summaries replace claims. Sources get summarized in a way that no longer traces back to what the paper actually says.

Both failures are bookkeeping failures. The first is a maintenance problem (who keeps the structure healthy?). The second is a provenance problem (where did this claim come from?).

Memoria addresses both: the agent handles the maintenance discipline that humans consistently avoid; the vault structure enforces provenance.

---

## Autonomy boundary

Memoria targets multi-step execution under human-set strategy and review. The
agent can do unattended work inside a request; the PI still decides what becomes
canonical. The full autonomy argument lives in
[Why Memoria doesn't pursue full autonomy](../boundaries/why-not-autonomous.md).

---

## Related

**Explanation**

- The intellectual roots of the design: [Intellectual foundations](intellectual-foundations.md)
- The seven-layer architecture: [Architecture](../../explanation/architecture/README.md)
- Why the human gate is structural: [Why the review gate is structural](../boundaries/why-review-gate-is-structural.md)
- Why L3 is the ceiling: [Why Memoria doesn't pursue full autonomy](../boundaries/why-not-autonomous.md)
- The principles this framing produces: [Design principles](design-principles.md)

**Reference**

- Term lookup for the jargon used here: [Glossary](../../reference/glossary.md)
