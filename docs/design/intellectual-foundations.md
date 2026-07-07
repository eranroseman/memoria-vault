---
title: Intellectual foundations
parent: Design Book
grand_parent: Developers
nav_order: 2
---

# Intellectual foundations

Memoria is built on four converging ideas and informed by a full review of ~400 papers spanning contemporary AI-research systems and the HCI, extraction, evaluation, and retrieval traditions they build on. Understanding where the design comes from makes it easier to understand why specific choices were made.

---

## Karpathy's LLM-Wiki pattern

[Andrej Karpathy](../reference/bibliography.md#karpathy-llm-wiki) proposed an AI agent that compiles raw sources into a persistent, interlinked Markdown wiki. The key move is replacing _retrieval from scratch at query time_ with a _persistent wiki that grows with use_.

In standard retrieval-augmented generation, every question triggers a fresh search over raw documents. Useful synthesis is never stored; nothing compounds. The LLM-wiki pattern inverts this: the agent builds durable pages, and each new source improves those pages rather than sitting in isolation. The agent is a **compiler**, not just a retriever.

Memoria takes this insight seriously. The vault is the compiled artifact. Ingest
doesn't just add documents — it integrates source Works into an existing graph
of notes. Digest, note, and hub operations do the compilation work.

What Memoria doesn't take from this pattern: Karpathy's framing implies an agent that autonomously decides what to synthesize and what to keep. Memoria refuses that — the human decides what enters the canonical graph. The compiler role belongs to the agent; the editorial role belongs to the human.

---

## Luhmann's Zettelkasten

[Niklas Luhmann](../reference/bibliography.md#luhmann-zettelkasten)'s slip-box method enforces three disciplines that prevent a wiki from becoming an undifferentiated pile:

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

## Bush's Memex

[Vannevar Bush](../reference/bibliography.md#bush1945)'s Memex matters here for
one design move: durable associative trails. Memoria implements that as
wikilinks, typed relations, entity links, and hubs; folders stay secondary. A
claim note that has no incoming links has not entered the knowledge graph.

---

## The literature review

The ~400-paper review (`_papers/`) grounds the design in what the field has tried: AI-research systems, HCI/CSCW, extraction and claim verification, evaluation, and temporal retrieval.

Its main result is convergence. Separate research lines re-derive the structural
review gate, durable vault-as-memory, explicit tool/write boundaries,
deterministic ingest, and stage-gated handoffs. Alpha.19 implements that through
the standalone CLI/engine, read API, request envelope, runtime policy, and
trusted writer; MCP is optional transport context, not the core sandbox. The
review also scopes what Memoria rejects: advisory-only LLM review, scalar
keep/revert loops, and tree search over synthesis.

The pattern-by-pattern judgment is in [Pattern provenance table](../reference/pattern-provenance.md). The confident-wrong argument behind the human gate is in [Why the review gate is structural](why-review-gate-is-structural.md).

---

## The synthesis

Memoria takes Karpathy's compiler insight, Luhmann's typed-note discipline, Bush's associative memory, and the operational patterns of contemporary AI-research systems as a single design stack:

- The wiki is the compiled artifact (Karpathy).
- The document types preserve atomicity and lifespan distinction (Zettelkasten).
- The associative graph (wikilinks, hubs, entity links) preserves trails (Memex).
- The stage-gated pipeline and explicit agent roles come from the field survey.
- The AI agent provides the maintenance discipline that all three earlier traditions required from the human.

The design is not a novel invention — it is an integration of patterns that already existed, applied to a specific problem (single-researcher knowledge production) that none of the surveyed systems addressed directly.

---

## Related

- What the foundations produced: [Design principles](design-principles.md)
- Full borrow/adapt/ignore breakdown: [Pattern provenance table](../reference/pattern-provenance.md)
- What Memoria is: [What Memoria is](what-memoria-is.md)
- The layered architecture (structural form of thin-control-thick-state): [Architecture](../explanation/architecture/README.md)
- Why the autonomy boundary is where it is: [Why Memoria doesn't pursue full autonomy](why-not-autonomous.md)
