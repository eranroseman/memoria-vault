---
title: "Pattern provenance: borrow, adapt, ignore"
parent: Design Book
grand_parent: Developers
nav_order: 30
---

# Pattern provenance: borrow, adapt, ignore

*Pattern provenance* records where each design pattern came from and what Memoria did with it: borrowed, adapted, used only as framing, or refused.

The distinction matters because many autonomous-scientist systems pair useful mechanics with an autonomy posture Memoria rejects. Provenance keeps those separate: a reader can see whether a pattern was omitted by ignorance or by judgment.

So each pattern Memoria encountered is sorted into one of four verdicts:

- **Borrow** — adopted as-is; the mechanic solved a real problem and needed no change.
- **Adapt** — the mechanic is kept, but the *autonomy posture* is narrowed; Memoria refuses the scalar-metric keep/revert loop most of these systems run on top.
- **Reference** — informs framing or positioning without contributing a borrowable pattern (surveys, position papers, taxonomies).
- **Ignore** — evaluated and explicitly refused; each refusal is a specific judgment, not a default.

The evidence base is a ~47-system survey inside a wider ~400-paper review (`_papers/`, verdicts in `_papers/REVIEW-SUMMARY.md`). This page keeps only the four verdicts and representative examples.

The headline patterns are summarized in [Intellectual foundations](intellectual-foundations.md). The autonomy boundary that rejects several patterns wholesale is in [Why Memoria doesn't pursue full autonomy](why-not-autonomous.md).

---

## Borrow: structural patterns adopted as-is

The borrowed patterns are mechanics Memoria takes unchanged:

| Pattern | Representative sources | Memoria use |
| --- | --- | --- |
| Stage-gated pipeline | ResearchArena, MLR-Copilot, AutoResearchClaw | Library intake and Project output run as distinct stages with validated handoffs. |
| Explicit roles per agent | [AI Scientist v2](../reference/bibliography.md#yamada2025aiscientistv2), [LatteReview](../reference/bibliography.md#rouzrokh2026lattereview), [Agent Laboratory](../reference/bibliography.md#schmidgall2025agentlaboratory) | Five permission-scoped Hermes profiles; see [Why specialist profiles](why-specialist-profiles.md). |
| Strong schema at handoffs | AI Scientist, AutoResearchClaw | Typed frontmatter catches mismatches that free-text handoffs would compound. |
| Persistent knowledge graph | [OmegaWiki](../reference/bibliography.md#qian2026omegawiki), Idea2Story | Wikilinks, typed relations, hubs, and entity notes. |
| Reviewable organization artifacts | LitLLM, [LatteReview](../reference/bibliography.md#rouzrokh2026lattereview) | Canvases, hubs, and Bases views keep synthesis visible. |
| Persistent Kanban + worker lanes | Hermes Agent | The durable board where background lanes claim work; see [Why Hermes](why-hermes.md). |
| Durable-state thesis | [Chen et al. 2026](../reference/bibliography.md#chen2026autonomous), [MetaGPT](../reference/bibliography.md#hong2024metagpt), [PARNESS](../reference/bibliography.md#wang2026parness) | Thin control over thick state; supporting numbers are in [Why the architecture is layered](why-three-layers.md). |
| Claim-to-evidence chain | [ScientistOne](../reference/bibliography.md#meng2026scientistone), [AutoResearchClaw](../reference/bibliography.md#liu2026autoresearchclaw) | Peer-reviewer claim-trace and citation checks. |
| Point-of-action discovery | Karpathy Autoresearch | Deferred nightly Librarian discovery with bounded batch size. |

---

## Adapt: mechanic kept, autonomy stripped

The adapted patterns share one shape: the mechanic is worth borrowing, but the system that originated it bolts on an autonomous quality loop that Memoria removes, leaving the human as the stopping criterion.

| Mechanic kept | Source | Autonomy removed |
| --- | --- | --- |
| Discover/select/organize pipeline | ResearchArena | "Organize" becomes human distillation. |
| Modular planner/writer/code roles | [AI Scientist](../reference/bibliography.md#lu2024aiscientist), [AI Scientist v2](../reference/bibliography.md#yamada2025aiscientistv2) | Tree search over synthesis. |
| Memory + meta-review | [AI co-scientist](../reference/bibliography.md#gottweis2025aicoscientist) | Tournament and evolution loop. |
| Inspiration retrieval before drafting | [SciMON](../reference/bibliography.md#wang2024scimon) | Novelty optimizer. |
| Hypothesis-feedback taxonomy | [MOOSE](../reference/bibliography.md#yang2026moose) | Autonomous judgment; used as a verification rubric. |
| Chain-of-Evidence taxonomy | [ScientistOne](../reference/bibliography.md#meng2026scientistone) | Score-as-gate; reserved for Peer-reviewer claim trace. |
| Scenario-typed retrieval | [PARNESS](../reference/bibliography.md#wang2026parness) | Extended relation vocabulary remains deferred. |
| Per-paper structured representation | [Knows](../reference/bibliography.md#yu2026knows) | Automatic ingest population; `_aspects.*` slots exist. |
| Consensus pre-filter, benchmarks, shared synthesis pool, trace capture, systematic review mode | [AI-Supervisor](../reference/bibliography.md#long2026aisupervisor), [CiteME](../reference/bibliography.md#press2024citeme), [AutoResearchBench](../reference/bibliography.md#xiong2026autoresearchbench), [AgentRxiv](../reference/bibliography.md#schmidgall2025agentrxiv), LatteReview, LitLLM | Any score or pre-filter can change what reaches the gate, never where the gate sits. |

---

## Reference: framing, not patterns

| Framing source | What it contributes |
| --- | --- |
| [Chen 2026](../reference/bibliography.md#chen2026copilots), *From Copilots to Colleagues* | L1-L5 autonomy vocabulary; Memoria targets L3 with a structural ceiling. |
| [Feng and Liu 2026](../reference/bibliography.md#feng2026visionary) | "Vibe researching" language: human as creative director and quality gatekeeper. |
| Deep Research surveys ([Huang et al. 2025](../reference/bibliography.md#huang2025deepresearch); [Xu and Peng 2025](../reference/bibliography.md#xu2025deepresearch)) | Contrast case: query-driven, ephemeral reports are not Memoria. |
| [Gridach et al. 2025](../reference/bibliography.md#gridach2025agentic), [Bisht et al. 2026](../reference/bibliography.md#bisht2026agentic) | Collaborative rather than autonomous positioning; persistent world-model support. |
| [Yue et al. 2026](../reference/bibliography.md#yue2026mcpnative) | Durable shared artifacts in MCP-native ecosystems; Memoria adds MCP as a permission boundary. |
| [Zhang et al. 2026](../reference/bibliography.md#zhang2026howfar) | Artifact-aware review supports the evidence-grounded Peer-reviewer and blocking gate. |
| [Qi et al. 2023](../reference/bibliography.md#qi2023hypothesis), [Ren et al. 2025](../reference/bibliography.md#ren2025scientific) | Narrow inputs for future domain-science or diversity-tuning work. |

---

## Ignore: patterns evaluated and refused

Almost every refusal traces to a scalar-optimization loop with no blocking human gate:

| Refused pattern | Example sources | Reason |
| --- | --- | --- |
| Full autonomous scientist mode | [AI Scientist v2](../reference/bibliography.md#yamada2025aiscientistv2), Sibyl, AI-Researcher, Auto-Research | Runs end-to-end without Memoria's structural gate. |
| Tree search over synthesis | AIDE ML, AI Scientist v2 | Requires a fixed scalar metric; synthesis quality is not scalar. |
| Autonomous keep/revert | Karpathy Autoresearch | The three safe-loop preconditions fail for knowledge work. |
| Co-trained generator + reviewer | [CycleResearcher](../reference/bibliography.md#weng2025cycleresearcher) | The reviewer's learned preferences become the objective. |
| Tournament/evolution loop | [AI co-scientist](../reference/bibliography.md#gottweis2025aicoscientist) | Sound memory architecture, refused autonomy posture. |
| Preferences internalized into weights | [NanoResearch](../reference/bibliography.md#xu2026nanoresearch) | Preferences stop being inspectable, auditable, or revertible. |
| Confidence-routed gate bypass | AutoResearchClaw SmartPause | Turns a structural gate into a probabilistic one. |
| Harness without a gate | [Sibyl-AutoResearch](../reference/bibliography.md#wang2026sibyl) | Harness rhetoric does not imply human control. |
| Conversation as durable substrate | [AutoGen](../reference/bibliography.md#wu2023autogen) | Conversation is ephemeral; the vault is memory. |
| Generalist sandboxed dev worker | [OpenHands](../reference/bibliography.md#wang2025openhands) | Permission model is too coarse for per-zone, per-profile policy. |

The full autonomy argument is in [Why Memoria doesn't pursue full autonomy](why-not-autonomous.md).

---

## Cross-cutting findings from the full literature review

The wider ~400-paper review adds few new end-to-end patterns, but sharpens several cross-cutting rules:

| Finding | Sources | Design effect |
| --- | --- | --- |
| Generator-verifier, sample-and-rank | [Cobbe et al. 2021](../reference/bibliography.md#cobbe2021verifiers), [Perez et al. 2022](../reference/bibliography.md#perez2022modelwritten) | Formalizes "engines write, agents judge" at claim grain. |
| Evidence-grounded verification | [FEVER](../reference/bibliography.md#thorne2018fever) | Build supports/contradicts on entailment plus recorded warrant, not embedding cosine. |
| Temporal coverage | [TEMPO](../reference/bibliography.md#abdallah2026tempo) | Treat supersession and evidence date as load-bearing retrieval dimensions. |
| HCI lineage of the gate | [Horvitz](../reference/bibliography.md#horvitz1999mixedinitiative), [Find-Fix-Verify](../reference/bibliography.md#bernstein2010soylent), [Amershi](../reference/bibliography.md#amershi2019guidelines), [Ackerman](../reference/bibliography.md#ackerman2000cscw) | Keeps the PI as adjudicator; separates generation from verification. |
| Indirect-prompt-injection hardening | [Greshake et al.](../reference/bibliography.md#greshake2023injection), [AgentDojo](../reference/bibliography.md#debenedetti2024agentdojo) | Confirms least-privilege tool allowlists and MCP-only sandbox. |
| Fluency is not evidence | [Bender et al. 2021](../reference/bibliography.md#bender2021parrots) | Keeps uncertainty flags and source-span provenance on atomic claims. |

These reinforce existing design lines: the Peer-reviewer's evidence chain, the structural gate, and the MCP sandbox.

---

## Net effect

The design shift versus a generic "agent-assisted knowledge base" is from agent-assisted to **bounded, phase-gated knowledge production**:

- The agent becomes better at bookkeeping, retrieval, and drafting.
- The human remains the gatekeeper for meaning, promotion, and final structure.
- Every borrowed pattern is adopted for its mechanic; every scalar-optimization loop that sits on top of that mechanic is stripped.

This makes the architecture more reliable (errors surface at phase gates), easier to debug (each phase has traceable responsibility), and less likely to accumulate polished but untrusted content (nothing reaches canonical without human approval).

---

## The underlying survey

The full survey is not inline on this page. The ~47-system agent-research slice and the wider ~400-paper corpus live in `_papers/` (Zotero export `_papers/Exported Items.bib`) with verdicts in `_papers/REVIEW-SUMMARY.md`. This page keeps only the design conclusions and representative citations.

---

## Related

- Where the corpus pushes back on these bets: [What the literature pushes back on](what-the-literature-pushes-back-on.md)
- The principles this survey operationalizes: [Design principles](design-principles.md)
- What Memoria is, in system terms: [What Memoria is](what-memoria-is.md)
