---
title: Pattern provenance table
parent: Evidence and integrations
nav_order: 2
grand_parent: Reference
---

# Pattern provenance table

Lookup table for the AI-research-system patterns Memoria borrowed, adapted,
used as framing, or rejected. The design argument is
[Pattern provenance: borrow, adapt, ignore](../../explanation/rationale/evidence/why-pattern-provenance.md).

## Borrow

| Pattern | Representative sources | Memoria use |
| --- | --- | --- |
| Stage-gated pipeline | [ResearchArena](bibliography.md#kang2024researcharena), [MLR-Copilot](bibliography.md#li2025mlrcopilot), AutoResearchClaw | Library intake and Project output run as distinct stages with validated handoffs. |
| Explicit roles per operation | [AI Scientist v2](bibliography.md#yamada2025aiscientistv2), [LatteReview](bibliography.md#rouzrokh2026lattereview), [Agent Laboratory](bibliography.md#schmidgall2025agentlaboratory) | Permission-scoped operation manifests and request rows. |
| Strong schema at handoffs | AI Scientist, AutoResearchClaw | Typed frontmatter catches mismatches that free-text handoffs would compound. |
| Persistent knowledge graph | [OmegaWiki](bibliography.md#qian2026omegawiki), [Idea2Story](bibliography.md#xu2026idea2story) | Wikilinks, typed relations, hubs, and entity notes. |
| Reviewable organization artifacts | LitLLM, [LatteReview](bibliography.md#rouzrokh2026lattereview) | Canvases, hubs, and optional editor views keep synthesis visible. |
| Persistent work queue | Hermes Agent | Historical inspiration; the standalone runtime uses operation requests in the workspace DB. |
| Durable-state thesis | [Chen et al. 2026](bibliography.md#chen2026autonomous), [MetaGPT](bibliography.md#hong2024metagpt), [PARNESS](bibliography.md#wang2026parness) | Thin control over thick state. |
| Claim-to-evidence chain | [ScientistOne](bibliography.md#meng2026scientistone), [AutoResearchClaw](bibliography.md#liu2026autoresearchclaw) | Peer-reviewer claim-trace and citation checks. |
| Point-of-action discovery | Karpathy Autoresearch | Provider-discovered Work candidates surface as unchecked attention and exploration-channel items. |

## Adapt

| Mechanic kept | Source | Autonomy removed |
| --- | --- | --- |
| Discover/select/organize pipeline | [ResearchArena](bibliography.md#kang2024researcharena) | "Organize" becomes human distillation. |
| Modular planner/writer/code roles | [AI Scientist](bibliography.md#lu2024aiscientist), [AI Scientist v2](bibliography.md#yamada2025aiscientistv2) | Tree search over synthesis. |
| Memory + meta-review | [AI co-scientist](bibliography.md#gottweis2025aicoscientist) | Tournament and evolution loop. |
| Inspiration retrieval before drafting | [SciMON](bibliography.md#wang2024scimon) | Novelty optimizer. |
| Hypothesis-feedback taxonomy | [MOOSE](bibliography.md#yang2026moose) | Autonomous judgment; used as a verification rubric. |
| Chain-of-Evidence taxonomy | [ScientistOne](bibliography.md#meng2026scientistone) | Score-as-gate; reserved for Peer-reviewer claim trace. |
| Scenario-typed retrieval | [PARNESS](bibliography.md#wang2026parness) | Memoria keeps the current authored relation vocabulary narrow: `supports`, `contradicts`, and `extends`. |
| Per-paper structured representation | [MASSW](bibliography.md#zhang2024massw), [Knows](bibliography.md#yu2026knows) | Five-aspect schema (context/key-idea/method/outcome/projected-impact) drives automatic ingest population; `work_aspects` read-model rows are queryable. |
| Consensus pre-filter, benchmarks, shared synthesis pool, trace capture, systematic review mode | [AI-Supervisor](bibliography.md#long2026aisupervisor), [CiteME](bibliography.md#press2024citeme), [AutoResearchBench](bibliography.md#xiong2026autoresearchbench), [AgentRxiv](bibliography.md#schmidgall2025agentrxiv), LatteReview, LitLLM | Scores can change what reaches the gate, never where the gate sits. |

## Reference

| Framing source | What it contributes |
| --- | --- |
| [Chen 2026](bibliography.md#chen2026copilots), *From Copilots to Colleagues* | L1-L5 autonomy vocabulary; Memoria targets L3 with a structural ceiling. |
| [Feng and Liu 2026](bibliography.md#feng2026visionary) | "Vibe researching" language: human as creative director and quality gatekeeper. |
| Deep Research surveys ([Huang et al. 2025](bibliography.md#huang2025deepresearch); [Xu and Peng 2025](bibliography.md#xu2025deepresearch)) | Contrast case: query-driven, ephemeral reports are not Memoria. |
| [Gridach et al. 2025](bibliography.md#gridach2025agentic), [Bisht et al. 2026](bibliography.md#bisht2026agentic) | Collaborative rather than autonomous positioning; persistent world-model support. |
| [Yue et al. 2026](bibliography.md#yue2026mcpnative) | Durable shared artifacts in MCP-native ecosystems; Memoria applies the same artifact discipline through the standalone engine/read API, with MCP only as an optional scoped transport. |
| [Zhang et al. 2026](bibliography.md#zhang2026howfar) | Artifact-aware review supports the evidence-grounded Peer-reviewer and blocking gate. |
| [Qi et al. 2023](bibliography.md#qi2023hypothesis), [Ren et al. 2025](bibliography.md#ren2025scientific) | Boundary examples for domain-science and diversity-tuning work outside the current product scope. |

## Ignore

| Refused pattern | Example sources | Reason |
| --- | --- | --- |
| Full autonomous scientist mode | [AI Scientist v2](bibliography.md#yamada2025aiscientistv2), Sibyl, AI-Researcher, Auto-Research | Runs end-to-end without Memoria's structural gate. |
| Tree search over synthesis | [AIDE ML](bibliography.md#aideml), AI Scientist v2 | Requires a fixed scalar metric; synthesis quality is not scalar. |
| Autonomous keep/revert | Karpathy Autoresearch | The three safe-loop preconditions fail for knowledge work. |
| Co-trained generator + reviewer | [CycleResearcher](bibliography.md#weng2025cycleresearcher) | The reviewer's learned preferences become the objective. |
| Tournament/evolution loop | [AI co-scientist](bibliography.md#gottweis2025aicoscientist) | Sound memory architecture, refused autonomy posture. |
| Preferences internalized into weights | [NanoResearch](bibliography.md#xu2026nanoresearch) | Preferences stop being inspectable, auditable, or revertible. |
| Confidence-routed gate bypass | AutoResearchClaw SmartPause | Turns a structural gate into a probabilistic one. |
| Harness without a gate | [Sibyl-AutoResearch](bibliography.md#wang2026sibyl) | Harness rhetoric does not imply human control. |
| Conversation as durable substrate | [AutoGen](bibliography.md#wu2023autogen) | Conversation is ephemeral; the vault is memory. |
| Generalist sandboxed dev worker | [OpenHands](bibliography.md#wang2025openhands) | Permission model is too coarse for per-zone, per-profile policy. |

## Cross-cutting findings

| Finding | Sources | Design effect |
| --- | --- | --- |
| Generator-verifier, sample-and-rank | [Cobbe et al. 2021](bibliography.md#cobbe2021verifiers), [Perez et al. 2022](bibliography.md#perez2022modelwritten) | Formalizes "engines write, agents judge" at claim grain. |
| Evidence-grounded verification | [FEVER](bibliography.md#thorne2018fever) | Build supports/contradicts on entailment plus recorded warrant, not embedding cosine. |
| Temporal coverage | [TEMPO](bibliography.md#abdallah2026tempo) | Treat supersession and evidence date as load-bearing retrieval dimensions. |
| HCI lineage of the gate | [Horvitz](bibliography.md#horvitz1999mixedinitiative), [Find-Fix-Verify](bibliography.md#bernstein2010soylent), [Amershi](bibliography.md#amershi2019guidelines), [Ackerman](bibliography.md#ackerman2000cscw) | Keeps the PI as adjudicator; separates generation from verification. |
| Indirect-prompt-injection hardening | [Greshake et al.](bibliography.md#greshake2023injection), [AgentDojo](bibliography.md#debenedetti2024agentdojo) | Confirms least-privilege tool allowlists, runtime write policy, read scopes, and sealed untrusted-data prompt blocks. |
| Fluency is not evidence | [Bender et al. 2021](bibliography.md#bender2021parrots) | Keeps uncertainty flags and source-span provenance on atomic claims. |
