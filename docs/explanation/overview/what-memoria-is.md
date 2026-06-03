---
title: What Memoria is
parent: Overview
nav_order: 1
---


# What Memoria is

## The central insight

**Maintaining a knowledge base is a bookkeeping problem, not an intelligence problem.**

Humans are excellent at recognizing what matters and forming original arguments. They are poor at consistently updating summaries, patching broken links, filing useful answers, and running structural health checks. Those tasks are mechanical, repetitive, and easy to defer — and because they're deferred, knowledge bases stagnate. Notes pile up without synthesis; citations go unverified; gaps go unnoticed.

The AI agent is suited for exactly those bookkeeping tasks. Memoria's design follows from this: make the agent narrower and more reliable, and let the human do the irreducibly judgment-laden work. This is not a claim about agent capability — it's a claim about which tasks should be delegated.

---

## What Memoria is

Memoria is a **bounded, stage-gated knowledge production system** for a single researcher. Specifically:

**Bounded** means it operates within explicit limits on autonomy. The agent does not decide what is worth keeping; the human does. The agent does not promote claims to canonical knowledge; the human reviews and approves first. These limits are structural — enforced by the system's architecture, not by prompt instructions.

**Stage-gated** means work passes through defined stages with explicit outputs at each boundary. A source doesn't become a claim until it's been classified, discussed, and synthesized. A draft doesn't become a deliverable until it's been verified and approved. Each stage has a clear entry condition and a clear exit condition.

**Knowledge production** means the system is designed to *produce* knowledge, not just store it. The vault grows more useful over time: new sources connect to existing claims, synthesis sharpens as more evidence accumulates, and structural maintenance keeps the graph coherent. This is the difference between a research vault and a notes pile.

**Single researcher** means the design assumes one human who owns judgment. Review decisions, synthesis choices, and scope priorities all belong to that human. This is not a team tool.

---

## What Memoria is not

**Not an autonomous research scientist.** Contemporary AI research systems (AI Scientist, AI co-scientist, CORAL) run experiments end-to-end, generate papers without review, and promote outputs to canonical based on scalar metrics. Memoria declines this posture for knowledge work — synthesis quality is not scalar, and synthesis errors compound across everything that later cites them.

**Not a general-purpose chat assistant.** Chat history is ephemeral. Conversations are inputs to filing, not the substrate of memory. If a useful answer lives only in a chat transcript, it hasn't been captured.

**Not a Deep Research agent.** Deep Research tools (OpenAI DR, Gemini DR, Perplexity DR) are query-driven and ephemeral: they produce a comprehensive report per query and end. Memoria is corpus-curating and durable: the human builds a vault over months, and each session compounds with prior sessions. The two categories serve different needs.

**Not a single-agent system.** "One model does everything" produces an agent with unclear responsibility, ambiguous permission boundaries, and no separation between discovery and synthesis. Memoria explicitly avoids this. Seven specialist profiles, each with narrow permissions and a clear exit condition, replace one generalist.

**Not a team tool in its current form.** The design assumes one human reviewer who owns judgment about what enters the canonical vault. Multi-user review semantics are not in scope.

---

## The problem it solves

A research vault typically fails in one of two ways:

1. **Capture without synthesis.** Sources accumulate in the inbox and never move forward. Notes pile up but don't connect. The vault grows but doesn't compound.

2. **Synthesis without rigor.** Bullets replace citations. Summaries replace claims. Sources get summarized in a way that no longer traces back to what the paper actually says.

Both failures are bookkeeping failures. The first is a maintenance problem (who keeps the structure healthy?). The second is a provenance problem (where did this claim come from?).

Memoria addresses both: the agent handles the maintenance discipline that humans consistently avoid; the vault structure enforces provenance.

---

## Where it sits on the autonomy spectrum

[Feng et al. 2025](../../reference/bibliography.md#feng2025levels)'s (*Levels of Autonomy for AI Agents*) five-level taxonomy runs: L1 (code autocomplete) → L2 (multi-step with human approval per step) → L3 (multi-step autonomous under human-set strategy with per-batch review) → L4 (self-directed within a bounded domain) → L5 (fully self-directed).

**Memoria targets L3 with a structurally enforced ceiling.** Profiles execute multi-step work unattended within a card, but the human sets the strategy and the review gate blocks every promotion. L4 and L5 require autonomous keep/revert on synthesis, which fails for knowledge work — the reasoning is in [Why Memoria doesn't pursue full autonomy](../rationale/why-not-autonomous.md).

Two 2026 perspectives anchor this positioning. [Feng and Liu 2026](../../reference/bibliography.md#feng2026visionary) describe "vibe researching" — the human keeps the intellectual steering wheel while agents handle labor — as the appropriate posture for research. [Bisht et al. 2026](../../reference/bibliography.md#bisht2026agentic) argue current systems are co-scientists, not autonomous scientists, for structural reasons that sit upstream of capability. Memoria is vibe researching made durable (the vault) and gated (blocking review).

---

## Naming

**Memoria** — because the heart of the design is memory: not just collecting information, but building a memory architecture that compounds. The name signals continuity, durability, and the act of remembering as deliberate practice.

**Hermes** — the agent runtime. [Hermes Agent](https://hermes-agent.nousresearch.com/) is the messenger: it carries work between states, between profiles, and between the human and the vault. Memoria is what you keep; Hermes is who moves things.

---

## Related

**Explanation**

- The intellectual roots of the design: [Intellectual foundations](intellectual-foundations.md)
- The three-layer architecture: [Architecture](../architecture/README.md)
- Why the human gate is structural: [Why the review gate is structural](../rationale/why-human-gate.md)
- Why L3 is the ceiling: [Why Memoria doesn't pursue full autonomy](../rationale/why-not-autonomous.md)
- The principles this framing produces: [Design principles](design-principles.md)

**Reference**

- Term lookup for the jargon used here: [Glossary](../../reference/glossary.md)
