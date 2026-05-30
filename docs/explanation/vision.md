---
topic: general
---

# Vision

Unfamiliar terms are defined in [glossary.md](../reference/glossary.md).

## Purpose

Memoria exists to reduce the gap between reading, thinking, and producing. It treats the knowledge base as an evolving substrate rather than a pile of notes, and it treats workflow state as first-class rather than implicit.

## Central insight

**Maintaining a knowledge base is a bookkeeping problem, not an intelligence problem.**

Humans are excellent at recognizing valuable sources and forming original arguments. They are poor at consistently updating summaries, patching broken links, filing useful answers, and running structural health checks. The agent is built for exactly those tasks. The AI agent handles bookkeeping that humans consistently avoid; the human steers judgment and sourcing.

This insight is what justifies the entire architecture. If you believed knowledge work was mostly an intelligence problem, you would build a smarter agent and let it write canonical claims. Memoria's design says the opposite — make the agent narrower and more reliable, and let the human do the irreducibly judgment-laden work.

## Intellectual foundations

Memoria stands on three converging ideas:

### Karpathy's LLM-Wiki pattern

Andrej Karpathy's proposal: an AI agent compiles raw sources into a persistent, interlinked Markdown wiki. The key move is replacing *retrieval from scratch at query time* with a *persistent wiki that grows with use*. The agent is a **compiler**, not just a retriever.

In standard RAG, every question triggers a fresh search over raw documents. Useful synthesis is never stored; nothing compounds. The LLM-wiki pattern inverts this: the agent builds durable pages, and each new source improves those pages rather than sitting in isolation.

### Niklas Luhmann's Zettelkasten Method

The slip-box method enforces three disciplines that prevent a wiki from becoming an undifferentiated pile:

1. **Atomicity** — each note captures one idea, not a topic dump.
2. **Explicit linking** — notes earn their place by connecting to existing notes.
3. **Type distinction** — Luhmann distinguished *fleeting notes* (raw capture), *literature notes* (what a source says), and *permanent notes* (the human's own durable claim). Each serves a different function and has a different lifespan. Memoria preserves this three-way distinction, renaming two of the three for a software context (literature notes → `paper-note`, permanent notes → `claim-note`); fleeting notes keep their name (`fleeting-note`) — see [vault/README.md](vault/README.md).

Zettelkasten's weakness in modern workflows is that it is entirely human-maintained — the linking discipline breaks down under load. Memoria delegates the linking and filing work to the agent.

### Vannevar Bush's Memex

Bush's 1945 vision: a personal interconnected knowledge machine where *associations* are first-class objects. The agent maintains associations, surfaces connections, and preserves trails of inquiry that would otherwise disappear into chat history.

### Contemporary AI-research systems

A survey of 37 contemporary agent-driven research systems and benchmarks — spanning end-to-end autonomous research, multi-agent platforms, retrieval and citation benchmarks, hypothesis generation, domain-adapted models, Deep Research agents, and the surveys that organize the field (Chen 2026, Huang 2025, Xu & Peng 2025, Gridach 2025, Ren 2025) — grounds the design. **Every system named below is catalogued with its citation** in [architecture/why-pattern-provenance.md](architecture/why-pattern-provenance.md), which also holds the full roster and the borrow / adapt / ignore breakdown; this section names only the patterns Memoria takes from the corpus.

**Adopted patterns:**

- **Stage-gated pipelines** (LitSearch, ResearchArena, MLR-Copilot, Agent Laboratory) — distinct stages with distinct outputs and validation points. The dominant shape across every end-to-end system surveyed.
- **Thin control over thick state** (Chen 2026, AgentRxiv 2025, PARNESS 2026) — the control plane and workers carry minimal context; durable knowledge lives in files. Three independent results corroborate it, and Memoria's three-layer split is its structural form. The ablation figures and the full borrow-mapping are in [architecture/README.md §"Thin control over thick state"](architecture/README.md#thin-control-over-thick-state).
- **Explicit agent roles** (AI co-scientist, MetaGPT, MOOSE, Agent Laboratory) — separate specialists (planner, executor, reviewer, Writer) over a generalist. Memoria's seven Hermes profiles.
- **Structured outputs at handoffs** (MetaGPT, PARNESS) — agents produce typed structured outputs at inter-agent boundaries, not free text. Memoria's frontmatter schema + handoff payload.
- **Persistent knowledge graphs** (AI co-scientist's Memory module, AI-Supervisor's Research World Model, PARNESS, OmegaWiki) — typed relationships as primary memory, not RAG-only. Memoria's vault folders + frontmatter + wikilinks + MOC.
- **Reviewable organization artifacts** (AI co-scientist's Meta-review agent, LitLLM, LatteReview) — synthesis as inspectable output, not hidden in prompts.

**Adapted with narrowing** — Memoria takes the mechanic, refuses the autonomy posture:

- **Inspiration retrieval before drafting** (SciMON) — fetch related claims as drafting context. Memoria borrows the retrieval; refuses novelty score as a stopping criterion (human stops).
- **Tournament ranking for triage** (AI co-scientist) — parked as a future-direction for the candidate-triage stage if scalar relevance ordering proves insufficient at high inbox volume.
- **Scenario-typed retrieval** (PARNESS) — typing wikilinks for richer graph queries. The base relations (`supports` / `contradicts`) are now adopted (ADR-9); a wider vocabulary (`similar`, possibly `cross-domain` / `counter-intuitive`) remains the future expansion.

**Position in the field.** The 2025–2026 wave converges on Memoria's core architectural commitments without weakening them. Chen 2026 names persistent knowledge accumulation, reliable self-evaluation, and principled agent scaling as the **#1 barriers to L5 autonomy** — not raw capability. Memoria has the persistent-knowledge piece, accepts that self-evaluation cannot be fully reliable (hence the blocking human gate), and treats agent scaling as a profile-narrowing problem rather than a generalist-strengthening problem. PARNESS (Wang & Luan 2026) is the architecturally nearest twin in the entire corpus — the architectures are near-identical, with one defining difference: Memoria has a structurally blocking human gate, PARNESS is fully autonomous.

What Memoria *rejects* from these systems is just as defining as what it borrows — see [architecture/why-pattern-provenance.md](architecture/why-pattern-provenance.md) for the borrow / adapt / ignore table and [architecture/why-no-autonomous-synthesis.md](architecture/why-no-autonomous-synthesis.md) for the three boundaries that block adoption of autonomous-scientist patterns.

### The synthesis

Memoria takes Karpathy's compiler insight, Luhmann's typed-note discipline, Bush's associative memory, and the operational patterns of contemporary AI-research systems as a single design stack:

- The wiki is the compiled artifact (Karpathy).
- The note types preserve atomicity and lifespan distinction (Zettelkasten).
- The associative graph (wikilinks, MOCs, entity links) preserves trails (Memex).
- The stage-gated pipeline and explicit agent roles come from the AI-research systems survey.
- The AI agent provides the maintenance discipline that all three earlier traditions previously required from the human.

The system is designed for one user who wants:

- Rigorous provenance — every claim traces to a source, every promotion is auditable.
- Technology assistance — the AI agent handles the mechanical work of capture, enrichment, classification, and structural maintenance.
- A clear human review gate — nothing becomes canonical knowledge until a human approves it.

Memoria is built on the conviction that a research vault should grow more useful over time, not just larger. Compounding requires structure: stable note types, durable identifiers, explicit lifecycle states, and a knowledge graph that the human can trust because they curated it.

## Design goals

1. **Make capture, synthesis, and promotion distinct operations.** Each has its own input, output, and validation criteria. Collapsing them produces polished but untrusted content.
2. **Keep human judgment in the loop for classification, synthesis quality, and canonization.** Agents propose; humans decide.
3. **Use the AI agent for mechanical work and structured task execution.** Ingest, enrichment, candidate generation, cross-link suggestion, linting, drafting — all bounded by profile, lane, and review gate.
4. **Use Kanban as the shared state machine for task persistence, retries, and handoffs.** A card survives across sessions. A retry reuses the same card. A handoff carries context.
5. **Store durable knowledge in the vault, not in chat history.** Conversation is ephemeral. The vault is the memory.
6. **Prefer explicit over implicit.** Review is a state, not a comment. Ownership is a field, not a convention. Promotion is a move, not a tag.

## What Memoria is

- A bounded, stage-gated knowledge production system.
- A specialist multi-agent architecture (Hermes profiles) coordinated by a state machine (Kanban).
- A vault that distinguishes source material, claim material, reference material, and project material — by folder, not by topic.
- A single-user system, designed for a researcher who values control and provenance.
- A system where **the human review state is structurally blocking, not advisory.** A card cannot promote until the human sets `review_status` to `approved`. This is deliberate positioning: the surveyed contemporary autonomous-research systems (ResearchAgent, AI co-scientist, MOOSE, Agent Laboratory) use LLM-based reviewers that advise; few make a human gate structurally required. Memoria's blocking gate is the structural form of the human-judgment commitment.

## Position on the autonomy spectrum

Chen 2026 (*From Copilots to Colleagues: A Survey of Autonomous Research Agents*) proposes a five-level taxonomy: **L1** code autocomplete, **L2** multi-step assistant with human approval per step, **L3** multi-step autonomous execution under human-set strategy with per-batch review, **L4** self-directed within a bounded domain (the current frontier — AI Scientist, AI co-scientist), and **L5** fully self-directed research agendas (aspirational).

**Memoria targets L3 with a structurally enforced ceiling.** Profiles execute multi-step unattended within a card (Librarian discovers, ingests, enriches, classifies; the discovery loop runs nightly; the Coder lane runs experiment loops against scalar criteria), but the human sets the strategy (`research-directions.md`, `screening-protocol.md` (not yet authored; see implementation-status.md — deferred)) and the review state gates promotion. Within L3, Memoria pursues the within-boundary autonomy progression documented in [roadmap/autonomy-progression.md](../project/roadmap/autonomy-progression.md).

Memoria deliberately does not target L4 or L5. The boundary is structural: [architecture/why-no-autonomous-synthesis.md](architecture/why-no-autonomous-synthesis.md) refuses the scalar-metric optimization and autonomous keep/revert patterns that L4 systems rely on, because synthesis correctness is not scalar and synthesis changes are not reversible. The single exception is the Coder lane (where Chen 2026's three preconditions actually hold) — see [§"Scope: these boundaries apply to synthesis"](architecture/why-no-autonomous-synthesis.md#scope-these-boundaries-apply-to-synthesis).

Two 2026 papers name the same slot from the human-control side. Feng & Liu 2026 (*A Visionary Look at Vibe Researching*) place a five-point spectrum — Traditional → Tool-Assisted → AI for Science → **Vibe Researching** → Auto Research — and define vibe researching as the human keeping "the intellectual steering wheel" (creative director and quality gatekeeper) while agents handle the labor of literature work, implementation, and drafting. That is precisely Memoria's posture; **Memoria is vibe researching made durable (the vault) and gated (blocking review)**. Bisht et al. 2026 (*Agentic AI Scientists Are Not Built for Autonomous Scientific Discovery*) reach the L3 ceiling from the opposite direction — a position paper arguing that current systems are *co-scientists, not autonomous scientists*, for reasons (tacit/failure-knowledge gaps, preference-optimization diversity compression, single-turn benchmark invalidity) that sit upstream of scale. Its recommended remedy — a "persistent world model carrying epistemic state across an investigation" — is structurally what Memoria's vault already is. Both are positioning references, not borrowed patterns; see [architecture/why-pattern-provenance.md §Reference](architecture/why-pattern-provenance.md#reference).

## What Memoria is not

- Not an autonomous research scientist. It does not run experiments end-to-end, write papers without review, or self-promote synthesis to canonical knowledge.
- Not a general-purpose chat assistant. It is a vault-centered system; conversations are inputs to filing, not the substrate.
- Not a team tool in its current form. It assumes one human reviewer who owns judgment.
- Not a single-agent system. The design explicitly avoids "one model does everything" — each Hermes profile has narrow permissions and a clear exit condition.
- **Not a Deep Research agent.** "Deep Research" agents (OpenAI DR, Gemini DR, Perplexity DR, Grok DeepSearch) are query-driven and ephemeral — produce a comprehensive report per query, then end. Memoria is corpus-curating and durable — the human builds a vault over months, and each session compounds with prior sessions. The two categories serve different human needs; Memoria is the wrong tool for one-shot reports and the right tool for long-horizon research substrates. See Huang et al. 2025 and Xu & Peng 2025 for the DR-category taxonomy (both catalogued in [architecture/why-pattern-provenance.md §Reference](architecture/why-pattern-provenance.md#reference)).

## Patterns rejected

Memoria's adopted patterns are listed under [Intellectual foundations](#contemporary-ai-research-systems) above; the full borrow / adapt / ignore breakdown lives in [architecture/why-pattern-provenance.md](architecture/why-pattern-provenance.md). What Memoria *refuses* to adopt is defining in its own right:

- **Full open-ended autonomous scientist mode** — too broad, misaligned with the human-review philosophy. Memoria's [autonomy boundary](architecture/why-no-autonomous-synthesis.md) is structural, not configurable.
- **One-model-does-everything** — gives up the safety of separation. The seven profiles each have narrow permissions and a clear exit condition.
- **Tree-search over experiment code** — applicable to ML benchmarking, not knowledge work. Synthesis quality isn't a scalar metric.
- **Auto-promotion of synthesis to canonical** — defeats the point of the review gate. Promotion is always synchronous with human attention.
- **Advisory-only LLM review (the field default)** — most surveyed autonomous-research systems use LLM-based reviewers whose verdicts inform but do not gate promotion. Memoria refuses this pattern: the review state is a structural gate, not an advisory annotation. See the [What Memoria is](#what-memoria-is) bullet on blocking review for the positive form of the choice.

## Naming rationale

The system is named **Memoria** because the heart of the design is memory: not just collecting information, but building a memory architecture that compounds.

Memoria signals continuity, durability, and the act of remembering as deliberate. It is not a search engine, not a chat history, not a corpus — it is a curated memory.

Hermes Agent — The self-improving AI agent built by Nous Research — keeps its name. Hermes is the messenger: it carries work between states, between profiles, and between the human and the vault. The two names play well together: Memoria is what you keep; Hermes is who moves things.

## Top-level constraints

These are inviolable design constraints, not preferences:

- **Folders encode lifecycle stage, not subject area.** A paper note about HCI lives in `20-sources/01-papers/`, not in `HCI/`. Topics belong in frontmatter and links.
- **Canonical synthesis is human-owned.** `30-synthesis/01-claims/` is not auto-written. Agents can suggest links; humans write claims.
- **The review state must change before promotion.** No worker says "I'm finished" and that promotes the card. The human sets `review_status` to `approved`.
- **Paper notes are never overwritten by structure or code agents.** Provenance is preserved.
- **The agent logs what it changed and why.** Every action is reversible because every action is recorded.

## Audience

This document set assumes a reader who:

- Knows Obsidian's folder/frontmatter conventions.
- Is familiar with Zotero + Better BibTeX as a bibliographic backbone.
- Has at least passing familiarity with multi-agent systems (Claude Code, Hermes, MCP-style tooling).
- Wants to build, not just read about, a research system.

If any of those is unfamiliar, [vault/README.md](vault/README.md) and [obsidian-ui/README.md](obsidian-ui/README.md) will give the most concrete grounding; [architecture/README.md](architecture/README.md) and [profiles/README.md](profiles/README.md) require more background.

## Next

- For the architecture: [architecture/README.md](architecture/README.md).
- For day-one operational workflows: [workflows/README.md](../how-to/workflows/README.md).
