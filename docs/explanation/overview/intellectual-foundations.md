---
title: Intellectual foundations
parent: Overview
nav_order: 2
---

# Intellectual foundations

Memoria is built on four converging ideas and informed by a full review of ~400 papers spanning contemporary AI-research systems and the HCI, extraction, evaluation, and retrieval traditions they build on. Understanding where the design comes from makes it easier to understand why specific choices were made.

---

## Karpathy's LLM-Wiki pattern

[Andrej Karpathy](../../reference/bibliography.md#karpathy-llm-wiki) proposed an AI agent that compiles raw sources into a persistent, interlinked Markdown wiki. The key move is replacing _retrieval from scratch at query time_ with a _persistent wiki that grows with use_.

In standard retrieval-augmented generation, every question triggers a fresh search over raw documents. Useful synthesis is never stored; nothing compounds. The LLM-wiki pattern inverts this: the agent builds durable pages, and each new source improves those pages rather than sitting in isolation. The agent is a **compiler**, not just a retriever.

Memoria takes this insight seriously. The vault is the compiled artifact. Ingest doesn't just add documents — it integrates sources into an existing graph of notes. A new source note connects to existing claims through typed wikilinks. The Librarian profile's job is essentially compilation.

What Memoria doesn't take from this pattern: Karpathy's framing implies an agent that autonomously decides what to synthesize and what to keep. Memoria refuses that — the human decides what enters the canonical graph. The compiler role belongs to the agent; the editorial role belongs to the human.

---

## Luhmann's Zettelkasten

[Niklas Luhmann](../../reference/bibliography.md#luhmann-zettelkasten)'s slip-box method enforces three disciplines that prevent a wiki from becoming an undifferentiated pile:

**Atomicity** — each note captures one idea, not a topic dump. An atomic note can be moved, cited, and linked without carrying irrelevant context.

**Explicit linking** — notes earn their place by connecting to existing notes. A note that connects to nothing has not been integrated into the system; it is still just a document.

**Type distinction** — Luhmann distinguished _fleeting notes_ (raw capture), _literature notes_ (what a source says), and _permanent notes_ (the human's own durable claim). Each type has a different epistemic status and a different lifespan. Memoria preserves this three-way distinction under different names: `fleeting`, `source` (what the source says), and `claim` (what the human thinks). The rename reflects a software context; the distinction is unchanged.

Zettelkasten's weakness in modern workflows is that it is entirely human-maintained — the linking discipline breaks down under load. Memoria delegates the maintenance work to the agent. Classifying notes, detecting orphans, suggesting cross-links, enforcing schema — these are the tasks the Librarian and Linter handle. The _intellectual_ work of the Zettelkasten (writing claim notes, forming arguments, building hubs) remains human.

---

## Bush's Memex

[Vannevar Bush](../../reference/bibliography.md#bush1945)'s 1945 vision: a personal interconnected knowledge machine where _associations_ are first-class objects. The device would let a researcher leave "trails" through a document collection — associative links that persist and can be revisited.

What Bush identified is that memory is associative, not taxonomic. A subject-area folder structure doesn't model how thinking actually works. What makes a knowledge base useful is not whether items are correctly classified, but whether the associations between them are preserved.

Memoria's vault is the Memex made operational: the graph of wikilinks, typed relations, entity links, and hubs is the associative layer. The folders are a secondary organizational scheme; the graph is the primary one. A claim note that has no incoming links hasn't made it into the knowledge graph — it may as well not exist.

---

## The literature review

A full review of ~400 papers (`_papers/`, each read end-to-end and judged for what Memoria should adopt, borrow, or reject) grounds the design in what the field has actually tried. It subsumes an earlier ~47-system survey of agent-driven research platforms and extends across the bodies of work those systems sit on: the HCI/CSCW human-augmentation tradition (mixed-initiative interfaces, Find-Fix-Verify, the social-technical gap), faithful information-extraction and claim-verification methods, evaluation and benchmark discipline, and retrieval with temporal reasoning.

The headline finding is that this wider literature does not merely *permit* Memoria's design — it independently *re-derives* it. The structural review gate ("engines write, agents judge, PI approves"), the durable vault-as-memory, the MCP-only agent sandbox, and deterministic ingest are each re-arrived-at by separate research lines. The patterns Memoria borrows — stage-gated pipelines, thin control over thick state, explicit agent roles, structured outputs at handoffs, persistent knowledge graphs — recur across nearly every end-to-end system, and Memoria's layered split is the structural form of them. The review also fixes what Memoria *declines* (advisory-only LLM review, scalar-metric keep/revert, tree-search-over-synthesis) and contributes two sharpenings to the knowledge model: build contradiction and supersession on entailment rather than embedding similarity, and treat temporal coverage as a first-class retrieval dimension.

The pattern-by-pattern judgment — what was borrowed as-is, taken with the autonomy stripped, referenced for framing, or refused, plus the [cross-cutting findings](../rationale/why-pattern-provenance.md#cross-cutting-findings-from-the-full-literature-review) from the wider corpus — is in [Pattern provenance: borrow, adapt, ignore](../rationale/why-pattern-provenance.md); the confident-wrong argument behind the structural human gate is in [Why the review gate is structural](../rationale/why-human-gate.md).

---

## The synthesis

Memoria takes Karpathy's compiler insight, Luhmann's typed-note discipline, Bush's associative memory, and the operational patterns of contemporary AI-research systems as a single design stack:

- The wiki is the compiled artifact (Karpathy).
- The note types preserve atomicity and lifespan distinction (Zettelkasten).
- The associative graph (wikilinks, hubs, entity links) preserves trails (Memex).
- The stage-gated pipeline and explicit agent roles come from the field survey.
- The AI agent provides the maintenance discipline that all three earlier traditions required from the human.

The design is not a novel invention — it is an integration of patterns that already existed, applied to a specific problem (single-researcher knowledge production) that none of the surveyed systems addressed directly.

---

## Related

- What the foundations produced: [Design principles](design-principles.md)
- Full borrow/adapt/ignore breakdown: [Pattern provenance: borrow, adapt, ignore](../rationale/why-pattern-provenance.md)
- What Memoria is: [What Memoria is](what-memoria-is.md)
- The layered architecture (structural form of thin-control-thick-state): [Architecture](../architecture/README.md)
- Why the autonomy boundary is where it is: [Why Memoria doesn't pursue full autonomy](../rationale/why-not-autonomous.md)
