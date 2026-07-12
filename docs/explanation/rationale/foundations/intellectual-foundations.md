---
title: Intellectual foundations
parent: Foundations
grand_parent: Design rationale
nav_order: 2
---

# Intellectual foundations

Memoria stands on four pillars — each owning one layer with no overlap — and is
informed by a full review of ~400 papers spanning contemporary AI-research systems
and the HCI, extraction, evaluation, and retrieval traditions they build on:
**LLM-Wiki** (inflow), **Zettelkasten** (topology), **Toulmin** (logic), and
**autoresearch** (self-improvement). Understanding where the design comes from
makes it easier to understand why specific choices were made.

---

## Karpathy's LLM-Wiki pattern

[Andrej Karpathy](../../../reference/evidence-and-integrations/bibliography.md#karpathy-llm-wiki) proposed an AI agent that compiles raw sources into a persistent, interlinked Markdown wiki. The key move is replacing _retrieval from scratch at query time_ with a _persistent wiki that grows with use_.

In standard retrieval-augmented generation, every question triggers a fresh search over raw documents. Useful synthesis is never stored; nothing compounds. The LLM-wiki pattern inverts this: the agent builds durable pages, and each new source improves those pages rather than sitting in isolation. The agent is a **compiler**, not just a retriever.

Memoria takes this insight seriously. The vault is the compiled artifact. Ingest
doesn't just add documents — it integrates source Works into an existing graph
of notes. Digest, note, and hub operations do the compilation work.

What Memoria doesn't take from this pattern: Karpathy's framing implies an agent that autonomously decides what to synthesize and what to keep. Memoria refuses that — the human decides what enters the canonical graph. The compiler role belongs to the agent; the editorial role belongs to the human.

The idea is related in spirit to Vannevar Bush's [Memex](../../../reference/evidence-and-integrations/bibliography.md#bush1945) (1945) — a personal, curated knowledge store with associative trails between documents. Bush's vision was closer to this than to what the web became: private, actively curated, with the connections between documents as valuable as the documents themselves. The part he couldn't solve was who does the maintenance. The LLM handles that.

---

## Luhmann's Zettelkasten

[Niklas Luhmann](../../../reference/evidence-and-integrations/bibliography.md#luhmann-zettelkasten)'s slip-box method enforces three disciplines that prevent a wiki from becoming an undifferentiated pile:

**Atomicity** — each note captures one idea, not a topic dump. An atomic note can be moved, cited, and linked without carrying irrelevant context.

**Explicit linking** — notes earn their place by connecting to existing notes. A note that connects to nothing has not been integrated into the system; it is still just a document.

**Type distinction** — Luhmann distinguished _fleeting notes_ (raw capture),
_literature notes_ (what a source says), and _permanent notes_ (the human's own
durable claim). Each type has a different epistemic status and a different
lifespan. Memoria preserves the distinction as catalog Work, generated digest
Work, and PI-curated notes/hubs.

Zettelkasten's weakness in modern workflows is that it is entirely
human-maintained — the linking discipline breaks down under load. Memoria
delegates maintenance work to deterministic operations and bounded runners:
classifying Work, detecting orphans, suggesting cross-links, and enforcing
schema. The _intellectual_ work of the Zettelkasten (writing notes, forming
arguments, building hubs) remains human.

---

## Toulmin's argument model

Stephen Toulmin's model of argument (1958) gives the knowledge graph its logical basis. An argument decomposes into six roles — Claim, Grounds, Warrant, Backing, Qualifier, and Rebuttal — and Memoria makes those roles the *types* of the graph rather than leaving argument structure implicit in prose.

Typing the roles types the consequences: losing grounds, losing a warrant, a qualifier bounding a regression, and a rebuttal that strengthens when its target falls are different graph events with different blast radius. A graph that only stores "claim links to claim" cannot tell them apart; one that stores the Toulmin roles can. This is why Memoria assesses *grounding* rather than truth — the roles are the structure grounding is assessed against.

---

## The autoresearch loop

The fourth pillar is Karpathy's autoresearch framing — a fixed harness, one metric, keep-or-discard, run overnight — the self-improving trial-and-error loop that the contemporary [autoresearch systems](../../../reference/evidence-and-integrations/bibliography.md#liu2026autoresearchclaw) also pursue. Memoria applies it narrowly: to improve its *own instruments* — detectors, prompts, gates — by measuring a change against a frozen benchmark and keeping only what beats the bar.

The boundary is strict and load-bearing: autoresearch tunes the instruments that *assess* knowledge, never the knowledge itself. A self-improving loop pointed at the researcher's claims would optimize the vault toward whatever the metric rewards; pointed at the instruments, it sharpens the tools while the human keeps authorship of what they measure.

---

## The literature review

The ~400-paper review grounds the design in what the field has tried:
AI-research systems, HCI/CSCW, extraction and claim verification, evaluation,
and temporal retrieval. The published evidence is the cited
[Bibliography](../../../reference/evidence-and-integrations/bibliography.md) and the
[Pattern provenance table](../../../reference/evidence-and-integrations/pattern-provenance.md).

Its main result is convergence. Separate research lines re-derive the structural
review gate, durable vault-as-memory, explicit tool/write boundaries,
deterministic ingest, and stage-gated handoffs. The current standalone product
implements that through the CLI/engine, read API, request envelope, runtime
policy, and trusted writer; MCP is optional transport context, not the core sandbox. The
review also scopes what Memoria rejects: advisory-only LLM review, scalar
keep/revert loops, and tree search over synthesis.

The pattern-by-pattern judgment is in [Pattern provenance table](../../../reference/evidence-and-integrations/pattern-provenance.md). The confident-wrong argument behind the human gate is in [Why the review gate is structural](../boundaries/why-review-gate-is-structural.md).

---

## The synthesis

Memoria takes Karpathy's compiler insight, Luhmann's typed-note discipline, Toulmin's argument roles, and Karpathy's autoresearch loop — together with the operational patterns of contemporary AI-research systems — as a single design stack:

- The wiki is the compiled artifact, with its associative trails (Karpathy, after Bush's Memex).
- The document types preserve atomicity and lifespan distinction (Zettelkasten).
- The argument roles type the knowledge graph and its consequence propagation (Toulmin).
- The self-improvement loop sharpens Memoria's own instruments, never its knowledge (autoresearch).
- The stage-gated pipeline and explicit agent roles come from the field survey.
- The AI agent provides the maintenance discipline that the earlier traditions required from the human.

The design is not a novel invention — it is an integration of patterns that already existed, applied to a specific problem (single-researcher knowledge production) that none of the surveyed systems addressed directly.

---

## Related

- What the foundations produced: [Design principles](design-principles.md)
- Full borrow/adapt/ignore breakdown: [Pattern provenance table](../../../reference/evidence-and-integrations/pattern-provenance.md)
- What Memoria is: [What Memoria is](what-memoria-is.md)
- The layered architecture (structural form of thin-control-thick-state): [Architecture](../../architecture/README.md)
- Why the autonomy boundary is where it is: [Why Memoria doesn't pursue full autonomy](../boundaries/why-not-autonomous.md)
