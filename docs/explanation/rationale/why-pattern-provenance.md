---
title: "Pattern provenance: borrow, adapt, ignore"
parent: Design rationale
nav_order: 7
---

# Pattern provenance: borrow, adapt, ignore

Memoria draws on a broad survey of ~47 contemporary AI-research systems, platforms, and benchmarks. This document is the synthesized judgment table: what was borrowed as-is, what was taken with the autonomy stripped out, what informs framing without contributing a design pattern, and what was evaluated and explicitly refused.

The headline patterns are summarized in [Intellectual foundations](../overview/intellectual-foundations.md). The autonomy boundary that rejects several patterns wholesale is in [Why Memoria doesn't pursue full autonomy](why-not-autonomous.md).

---

## Borrow

Patterns adopted as-is. Each one solves a real problem; none required modification to fit Memoria's design.

| Pattern | Source | Why borrow it | Where it fits |
|---|---|---|---|
| **Stage-gated pipeline** | ResearchArena, MLR-Copilot, AutoResearchClaw | Prevents everything from collapsing into one giant prompt. Distinct stages with distinct outputs and validation points at each boundary are the dominant structural shape across every end-to-end system surveyed. | Compile: ingest → classify → discuss → synthesize. Compose: scope → frame → draft → verify → export. |
| **Explicit roles per agent** | [AI Scientist v2](../../reference/bibliography.md#yamada2025aiscientistv2), [LatteReview](../../reference/bibliography.md#rouzrokh2026lattereview), [Agent Laboratory](../../reference/bibliography.md#schmidgall2025agentlaboratory) | Keeps planning, execution, review, and writing separate. Each role has narrow permissions and traceable quality responsibility. | Five Hermes profiles; see [Why specialist profiles, not a generalist agent](why-specialist-profiles.md). |
| **Strong schema with validated handoffs** | AI Scientist, AutoResearchClaw | Structured outputs at inter-agent boundaries reduce cascading hallucinations and make automation debuggable. Free-text handoffs compound errors; typed frontmatter catches mismatches early. | Frontmatter namespaces, `_proposed_classification`, `_enrichment.*`, `_aspects.*`; see [Frontmatter fields](../../reference/frontmatter.md). |
| **Persistent knowledge graph** | [OmegaWiki](../../reference/bibliography.md#qian2026omegawiki), Idea2Story | Preserves relationships instead of re-searching at every query. The graph accumulates; each new source adds to an existing network rather than sitting in isolation. | Wikilinks, typed relations (`supports` / `contradicts`), MOCs, entity notes. |
| **Reviewable organization artifacts** | LitLLM, [LatteReview](../../reference/bibliography.md#rouzrokh2026lattereview) | Synthesis is inspectable, not hidden in prompts. The human can read and validate the organization layer independently of the content it organizes. | Canvases, MOCs, reference notes. |
| **Persistent Kanban + worker lanes** | Hermes Agent (Nous Research) | Durable state machine across sessions and retries. Work state persists when the session closes; the next worker picks up the card from its last known state. | Board layer; the background lanes claim cards; see [The board as a state machine (the control plane)](../workflows/board-as-state-machine.md). |
| **Point-of-action discovery loop** | Karpathy Autoresearch | Shifts discovery from reactive (user asks, agent searches) to proactive (scheduled overnight run, results ready for morning review). Bounded batch size prevents inbox overflow. | Nightly Librarian run with a bounded batch size; the scheduled loop is deferred — not yet active. |
| **File-as-Bus / thin control over thick state** | [Chen et al. 2026](../../reference/bibliography.md#chen2026autonomous) (*long-horizon engineering*) | Independent empirical validation: removing the durable-artifact bus drops PaperBench by 6.41 points and MLE-Bench Lite by 31.82 points. The persistent layer isn't overhead — it's the mechanism that makes long-horizon work possible. | The entire layered architecture; see [Why the architecture is layered](why-three-layers.md). |
| **Structured outputs at handoff boundaries** | [MetaGPT (Hong et al. 2024)](../../reference/bibliography.md#hong2024metagpt) | Independent validation that typed structured outputs at inter-agent boundaries (vs. free-text chat) reduce cascading hallucination across roles. | Frontmatter schema discipline; profile handoff contracts. |
| **Cross-run knowledge accumulation** | [PARNESS (Wang and Luan 2026)](../../reference/bibliography.md#wang2026parness) | Third independent corroboration of the durable-state thesis. PARNESS names "no existing tool persists cross-run knowledge in a form retrievable into a finite LLM context" as one of five structural problems in the field and addresses it with a persistent knowledge layer. | Vault layer; see [Why the architecture is layered](why-three-layers.md). |
| **Paper ↔ code repository linking** | [PARNESS (Wang and Luan 2026)](../../reference/bibliography.md#wang2026parness) | A paper's open-source repository is often the only complete specification of its experimental scheme; PARNESS makes the paper↔code correspondence a typed object in the knowledge graph. | Source enrichment: when ingesting a paper, search for and link its code repository when available. See [Profiles](../profiles/README.md). |
| **Claim-to-evidence chain by construction** | [ScientistOne (Meng et al. 2026)](../../reference/bibliography.md#meng2026scientistone), [AutoResearchClaw (Liu et al. 2026)](../../reference/bibliography.md#liu2026autoresearchclaw) | ScientistOne defines verifiability as "every claim traces through a recorded evidence chain to a grounding source" and reaches 0/337 hallucinated references where baselines hit up to 21%. AutoResearchClaw ties every reported number to a registry of executed outputs before it can enter a draft. A further independent corroboration of the durable-state thesis at the claim grain. | Peer-reviewer (verify lane): claim-trace and citation sub-checks. See [Profiles](../profiles/README.md). |

---

## Adapt

Patterns taken with modification. In each case, the mechanic is borrowed but the autonomy posture is narrowed: Memoria refuses the scalar-metric keep/revert loop that most of these systems layer on top.

| Pattern | Source | Why adapt it | How |
|---|---|---|---|
| **ResearchArena-style discover / select / organize** | ResearchArena | Good conceptual pipeline shape, but needs a deeper human synthesis layer. | Map to: find → capture → enrich → classify → discuss → distill → connect. The organize step becomes human-driven distillation, not agent-driven organization. |
| **AI Scientist modular roles** | AI Scientist [v1](../../reference/bibliography.md#lu2024aiscientist) + [v2](../../reference/bibliography.md#yamada2025aiscientistv2) (Sakana AI) | Useful role separation, but full autonomy is too broad for knowledge work. | Keep separate planner / writer / code-executor roles. Humans canonize. Tree-search over synthesis is refused (see Ignore). |
| **Memory module + Meta-review artifact** | [AI co-scientist (Gottweis et al. 2025)](../../reference/bibliography.md#gottweis2025aicoscientist) | The Memory store + Meta-review research-overview pair is the same shape as Memoria's vault + MOC. Architectural validation of vault-plus-roles design from the most production-mature system in the survey. | Vault layer; MOC type. The tournament / evolution loop on top of the Memory module is not adapted — see Ignore. |
| **Inspiration retrieval before drafting** | [SciMON (Wang et al. 2024)](../../reference/bibliography.md#wang2024scimon) | The "retrieve related prior ideas, then draft" mechanic improves grounding and reduces redundancy. The novelty optimizer (what drives keep/revert in SciMON) is refused. | Writer reads related claim notes as inspiration context before drafting. Novelty is not a stopping criterion — the human stops. |
| **Hypothesis-feedback taxonomy** | [MOOSE (Yang et al. 2024)](../../reference/bibliography.md#yang2026moose) | Three-channel feedback structure (present / past / future claim types) is a useful rubric for structuring verification prompts. | Borrowed as a prompt-design input for the Peer-reviewer; the autonomous quality gate that uses this taxonomy in MOOSE is not adopted. |
| **Citation-attribution benchmark** | [CiteME (Press et al. 2024)](../../reference/bibliography.md#press2024citeme) | Frontier LMs hit 4–18% on it; CiteAgent reaches 35%. Provides the Peer-reviewer a numeric regression target where there currently is none. | Deferred — the Peer-reviewer has no numeric acceptance criterion yet; this benchmark informs what that criterion should measure when it is defined. |
| **Agent-readable shared synthesis pool** | [AgentRxiv (Schmidgall and Moor 2025)](../../reference/bibliography.md#schmidgall2025agentrxiv) | Empirical: agents reading prior agent-generated reports gain ~11% on MATH-500 over isolated agents. Validates the Karpathy LLM-Wiki claim quantitatively with a benchmark. | Deferred — adopted in principle; cross-project reading requires enough corpus overlap across projects to be useful, which develops after the vault has been active for some months. |
| **Consensus pre-filter before human review** | [AI-Supervisor (Long 2026)](../../reference/bibliography.md#long2026aisupervisor) | Long's Research World Model commits findings only when multiple independent agents corroborate. A milder version of Memoria's blocking-review pattern — reduces review load without moving the autonomy boundary. The gate stays structural; pre-filtering only changes what reaches the gate. | Deferred — design calls for a lane-bounded prototype on the Librarian profile, with the Librarian's false-positive rate measured before broader adoption. |
| **Scenario-typed retrieval** | PARNESS (Wang & Luan 2026) | Richer than untyped wikilinks: `supports` / `contradicts` / `similar` / `cross-domain` / `counter-intuitive` relations enable queries like "show me evidence that contradicts this claim." | Base relations (`supports` / `contradicts`) are active: the Peer-reviewer uses them for claim-tracing and Dataview queries can filter on them. Extended vocabulary (`similar`, `cross-domain`, `counter-intuitive`) is deferred pending felt need. |
| **Chain-of-Evidence claim taxonomy** | [ScientistOne (Meng et al. 2026)](../../reference/bibliography.md#meng2026scientistone) | A claim taxonomy (`citation` / `numerical` / `methodological` / `conclusion`), each with a required evidence-chain shape and four integrity checks: score verification, specification violation, reference verification, method–code alignment. The citation and reference checks fit knowledge work directly. | Deferred — the Peer-reviewer's current checks cover citation resolution and claim-trace. The typed taxonomy and additional integrity checks are the intended next step once the claim-trace foundation is stable. Score-verification and method–code alignment are scoped to the Engineer's code lane only. |
| **Per-paper structured representation** | [Knows (Yu and Wang 2026)](../../reference/bibliography.md#yu2026knows) | A per-paper YAML sidecar that structures a paper into agent-readable fields lifts weak-model comprehension by +29–42 pp at lower token cost. Independent validation that structured paper representations (vs. raw PDF prose) help agents — which is what Memoria's source-note frontmatter already provides. | The `_aspects.*` frontmatter slots exist in the source-note template as the in-vault equivalent. Automatic population at ingest is deferred — the Librarian does not yet fill them. |
| **Literature-discovery benchmark** | [AutoResearchBench (Xiong et al. 2026)](../../reference/bibliography.md#xiong2026autoresearchbench) | Splits discovery into *deep* (find one specific paper) and *wide* (collect every paper meeting criteria) — the two modes the Librarian already runs. Provides a measurable target for discovery quality; the discovery-side analogue of what CiteME provides the Peer-reviewer. | Deferred — no eval harness exists yet. The vault's own corpus (papers with known relevance decisions) is the natural source when one is built. |
| **Exploration-trace capture** | ARA / The Last Human-Written Paper (Liu et al. 2026) | ARA's four-layer artifact preserves an exploration graph of rejected directions and dead ends alongside approved knowledge. The "Storytelling Tax" — narrative publication discards failure knowledge — is the same gap Memoria's vault has. | Deferred — the Librarian's map lane does not yet capture rejected directions. The intended form is a structured artifact alongside the corpus map, not a change to the vault's canonical knowledge structure. |
| **Multi-reviewer systematic review mode** | [LatteReview](../../reference/bibliography.md#rouzrokh2026lattereview), LitLLM | Strong pattern for formal systematic reviews; adds agent-driven screening and multi-reviewer agreement. Overkill for ongoing reading; valuable for bounded, protocol-driven synthesis projects. | Optional `review_mode: systematic-review` layer — deferred until a concrete systematic-review project surfaces demand. |

---

## Reference

Papers that inform framing or positioning without contributing a borrowable design pattern. Typically surveys, position papers, and taxonomies.

| Contribution | Source | Why referenced |
|---|---|---|
| **L1–L5 autonomy taxonomy** | [Chen 2026](../../reference/bibliography.md#chen2026copilots) (*From Copilots to Colleagues*) | Vocabulary for positioning Memoria precisely on the autonomy spectrum. Memoria targets L3 with a structurally enforced ceiling. See [What Memoria is](../overview/what-memoria-is.md). |
| **"Persistent knowledge accumulation is a primary barrier to L5 autonomy"** | [Chen 2026](../../reference/bibliography.md#chen2026copilots) (*From Copilots to Colleagues*) | Independent validation of Memoria's vault-as-load-bearing-piece thesis: a ~95-paper survey that names persistent knowledge accumulation (with self-evaluation and architecture scaling) as the critical barrier to L5 — exactly what Memoria's central commitment addresses. |
| **Deep Research as a sibling-but-distinct category** | [Huang et al. 2025](../../reference/bibliography.md#huang2025deepresearch); [Xu and Peng 2025](../../reference/bibliography.md#xu2025deepresearch) | Defines a category (query-driven, ephemeral-report agents like OpenAI DR / Gemini DR) that Memoria explicitly is not. Corpus-curating and durable vs. query-driven and ephemeral are different tools for different needs. |
| **Autonomous-vs-collaborative axis** | [Gridach et al. 2025](../../reference/bibliography.md#gridach2025agentic) | Positions Memoria unambiguously on the collaborative side. Survey findings that literature-review automation is the field's weakest sub-task reinforce the "agent does bookkeeping; human owns judgment" thesis. |
| **Co-scientist (not autonomous) thesis + four challenges** | [Bisht et al. 2026](../../reference/bibliography.md#bisht2026agentic) | Position paper concluding current agentic systems are co-scientists, not autonomous scientists. Its recommended "persistent world model carrying epistemic state across an investigation" is structurally the vault. Its hypothesis-hivemind finding (independent models converge semantically even when diversity is wanted) is a documented caution on the consensus pre-filter. |
| **"Vibe researching" human-control spectrum** | [Feng and Liu 2026](../../reference/bibliography.md#feng2026visionary) | Names the slot Memoria occupies — human as creative director and quality gatekeeper, agents handle labor — more crisply than Chen 2026's L1–L5. Memoria is vibe researching made durable (vault) and gated (blocking review). |
| **MCP-native ecosystem + durable shared artifacts** | [Yue et al. 2026](../../reference/bibliography.md#yue2026mcpnative) | Independently argues that scaling discovery needs an MCP-native interoperability substrate plus durable shared artifacts (task boards, lab notebooks, provenance stores) — which Memoria already has. Memoria's differentiator the perspective lacks: MCP as a *permission / policy boundary*, not merely interoperability. |
| **Artifact-aware review beats manuscript-only review** | [Zhang et al. 2026](../../reference/bibliography.md#zhang2026howfar) (*How Far Are We From True Auto-Research*) | A 117-paper audit showing manuscript-only reviewers are fooled by polished framing while artifact-aware review exposes fabrication. Empirical support for the evidence-grounded Peer-reviewer and the blocking human gate. |
| **Uncertainty-boosts-diversity finding** | [Qi et al. 2023](../../reference/bibliography.md#qi2023hypothesis) | A temperature-sampling observation for the overnight discovery loop: sample candidates at higher temperature, evaluate at lower. Not a design pattern; a tuning default. |
| **Scientific-agents survey** | [Ren et al. 2025](../../reference/bibliography.md#ren2025scientific) | Surveys LLM-based agents for domain science (chemistry, biology, materials). Relevant if Memoria's future directions explore domain-science applications; not a current commitment. |

---

## Ignore

Patterns evaluated and explicitly refused. Each refusal is a specific judgment, not a default.

| Pattern | Source | Why ignore |
|---|---|---|
| **Full autonomous scientist mode** | [AI Scientist v2](../../reference/bibliography.md#yamada2025aiscientistv2), Sibyl, AI-Researcher, Auto-Research | Misaligned with human-review philosophy. These systems run end-to-end without a blocking human gate per iteration; Memoria's gate is structural and non-negotiable. |
| **Tree search over synthesis** | AIDE ML, AI Scientist v2 (Yamada et al. 2025) | AI Scientist v2 demonstrates tree search produces peer-review-grade output — one v2 manuscript exceeded the human acceptance threshold at an ICLR workshop. The refusal is therefore a *fit judgment*, not a feasibility doubt. Tree search works when a scalar metric exists before the loop starts. Synthesis quality is not scalar; later sources reinterpret earlier ones. See [Why Memoria doesn't pursue full autonomy](why-not-autonomous.md). |
| **Autonomous keep / revert without review** | Karpathy Autoresearch | Synthesis correctness isn't scalar; synthesis changes aren't reversible; synthesis experiments aren't independent. The three preconditions that make autonomous loops safe for ML benchmarking all fail for knowledge work. See [Why Memoria doesn't pursue full autonomy](why-not-autonomous.md). |
| **Co-trained generator + reviewer loop** | [CycleResearcher (Weng et al. 2025)](../../reference/bibliography.md#weng2025cycleresearcher) | The reviewer LLM is RL-trained against human reviewers (26.89% MAE on paper scoring), then the generator is trained to maximize the reviewer's score. The metric is *learned* rather than fixed — as training proceeds, the reviewer's learned preferences become the loop's goal. Metric and objective collapse. The Peer-reviewer must remain prompt-driven against human-defined criteria; training it on human approvals risks the same collapse at smaller scale. |
| **Tournament / evolution loop** | AI co-scientist (Gottweis et al. 2025) | Self-improving hypothesis quality via ranking tournaments with no blocking human gate per iteration. The Memory/Meta-review pair from this system is *Adapt*; this loop on top is the same scalar-optimization shape Memoria refuses. Separating the two clarifies that the architectural pattern (persistent memory + structured artifacts) is sound; the autonomy posture on top of it is what Memoria refuses. |
| **Conversation as substrate** | [AutoGen (Wu et al. 2023)](../../reference/bibliography.md#wu2023autogen) | Inverts the central commitment that conversation is ephemeral and the vault is the memory. Adopting a chat-as-orchestrator runtime would route durable state through an inappropriate layer. The *conversation pattern* (humans in the loop via chat) is fine within an Agent Client pane; the *substrate* (chat as persistent memory) is not. |
| **Generalist sandboxed dev agent as drop-in worker** | [OpenHands (Wang et al. 2025)](../../reference/bibliography.md#wang2025openhands) | Strong runtime in isolation, but its permission model is sandbox-vs-host, not per-zone-per-profile. Adopting it as the Engineer's code runtime today would replace Memoria's lane-scoped policy MCP with a coarser boundary. Re-evaluate if a concrete code-lane limitation surfaces that Claude Code cannot address. |
| **Preference internalization into model weights** | [NanoResearch (Xu et al. 2026)](../../reference/bibliography.md#xu2026nanoresearch) | "Label-free policy learning" converts free-form human feedback into persistent parameter updates of the planner — preferences become weights. This is the co-trained-reviewer failure mode in a new form: once preferences live in weights they are no longer inspectable, auditable, or revertible, and the optimization target drifts silently. Memoria keeps personalization external and inspectable — vault content, lane-override files, configuration — never trained into model weights. |
| **Confidence-routed bypass of the human gate** | AutoResearchClaw SmartPause (Liu et al. 2026) | SmartPause routes a decision to the human only when the agent's self-assessed confidence is low. Adopting it for Memoria's blocking review would convert a structural gate into a probabilistic one. A confidently-wrong agent — the exact failure mode for hallucinated citations — would sail through. The HITL finding (targeted gating beats both extremes) is real, but was measured on a throughput-optimizing system where a bad output wastes a run. Memoria's vault is durable: a bad promotion persists and compounds. See [why-not-autonomous.md#why-not-confidence-routed-gating](why-not-autonomous.md). |
| **"Harness" framing that still removes the human gate** | [Sibyl-AutoResearch (Wang et al. 2026)](../../reference/bibliography.md#wang2026sibyl) | A 20-agent / 19-stage self-evolving pipeline built on Claude Code with no blocking human gate. The anti-paper-mill diagnosis is correct; the autonomy posture is the one Memoria refuses. The lesson worth recording: "harness" rhetoric does not imply a human gate. The gate is Memoria's differentiator, not the harness. |
| **One-model-does-everything** | (anti-pattern across early frameworks) | Loses the safety of permission separation. When one agent is responsible for everything, debugging requires re-reading the whole conversation; permissions become the superset of all tasks; the optimistic (discovery) and conservative (verification) stances cannot be structurally separated. |

---

## Net effect

The design shift versus a generic "agent-assisted knowledge base" is from agent-assisted to **bounded, stage-gated knowledge production**:

- The agent becomes better at bookkeeping, retrieval, and drafting.
- The human remains the gatekeeper for meaning, promotion, and final structure.
- Every borrowed pattern is adopted for its mechanic; every scalar-optimization loop that sits on top of that mechanic is stripped.

This makes the architecture more reliable (errors surface at phase gates), easier to debug (each phase has traceable responsibility), and less likely to accumulate polished but untrusted content (nothing reaches canonical without human approval).

---

## Systems surveyed

**Pipeline / role-based agent systems:** LitSearch, ResearchArena, SciLitLLM, LitLLM, LatteReview, ResearchAgent, Idea2Story, AI Scientist v1 (Lu et al. 2024), AI Scientist v2 (Yamada et al. 2025), Agent Laboratory, Sibyl, AutoResearchClaw (Liu et al. 2026), AI-Researcher, Auto-Research, OmegaWiki, CORAL, AIDE ML, MLR-Copilot, ScientistOne (Meng et al. 2026), ARA / The Last Human-Written Paper (Liu et al. 2026), Sibyl-AutoResearch (Wang et al. 2026).

**Persistent-knowledge / cross-run systems:** Karpathy Autoresearch, AI co-scientist (Gottweis et al. 2025), AiScientist long-horizon engineering (Chen et al. 2026), AgentRxiv (Schmidgall & Moor 2025), PARNESS (Wang & Luan 2026), AI-Supervisor (Long 2026), NanoResearch (Xu et al. 2026), Omni-SimpleMem (Liu et al. 2026).

**Retrieval, citation, structured handoffs:** SciMON (Wang et al. 2024), MOOSE (Yang et al. 2024), CiteME (Press et al. 2024), MetaGPT (Hong et al. 2024), ScientistOne (Meng et al. 2026), Knows (Yu & Wang 2026).

**Runtime and orchestration substrates:** AutoGen (Wu et al. 2023), OpenHands (Wang et al. 2025), CycleResearcher (Weng et al. 2025).

**Surveys, positions, and evaluations:** Gridach et al. (ICLR 2025), [Chen 2026](../../reference/bibliography.md#chen2026copilots) (*From Copilots to Colleagues*), Huang et al. 2025 (*Deep Research Agents*), Ren et al. 2025 (*Scientific Intelligence*), Xu & Peng 2025 (*Deep Research Systems*), MASSW (Zhang et al. 2024), Qi et al. 2023, Bisht et al. 2026 (*Not built for autonomous discovery*), Feng & Liu 2026 (*Vibe Researching*), Yue et al. 2026 (*MCP-native ecosystems*), Zhang et al. 2026 (*How Far Are We From True Auto-Research*), AutoResearchBench (Xiong et al. 2026).

---

## Related

- The principles this survey operationalizes: [Design principles](../overview/design-principles.md)
- What Memoria is, in system terms: [What Memoria is](../overview/what-memoria-is.md)
