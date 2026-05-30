---
topic: roadmap
---

# Benchmarks for evaluating Memoria

> *Updated 2026-05-29. arXiv IDs verified via the arXiv API; repo links verified via web search where shown.* The roadmap-level synthesis and design implications drawn from this taxonomy are in [evaluation.md](evaluation.md).

## Scoping principles

A capability-mapped taxonomy of benchmarks relevant (and deliberately *not* relevant) to Memoria. Organized by what each benchmark **measures**. Categories track Memoria's workflow pipeline in order — **upstream** capture (`find` → `ingest` → `classify`/`promote` → `distill`), **downstream** use (`frame`/`discuss` → `query`/`assess` → `code` → `verify` → `write`/`revise`), then **maintenance** (`lint`). Some capabilities are *not* pipeline steps — they're substrates or properties every workflow depends on — so they sit in a separate **Cross-cutting capabilities** group at the end. A benchmark belongs here only if it tests something Memoria is *designed to do*. Memoria is a **corpus-curating, human-gated, single-user research OS** — not an autonomous scientist and not a Deep Research agent. Six principles decide in-scope vs. out-of-scope:

1. **Capability match.** The task must correspond to a Memoria workflow (`find`, `ingest`, `classify`/`promote`, `distill`, `frame`/`discuss`, `query`/`assess`, `code`, `verify`, `write`/`revise`, `lint`) or memory tier. No workflow → out of scope.
2. **Curating, not query-ephemeral.** Memoria builds a durable vault over months. One-shot report generation (Deep Research) is the wrong shape → out of scope.
3. **Human-gated, not autonomous (L3 ceiling).** Promotion requires a human `approved` state. End-to-end autonomous discovery and auto-novelty scoring are refused → out of scope.
4. **Files, not weights.** Memoria's "knowledge update" edits Markdown files. Model-weight knowledge-editing benchmarks test a different mechanism → out of scope.
5. **Domain-general PKM.** Memoria is subject-agnostic. Domain-specific science benchmarks (protein, polymer, climate, clinical, research-math) are out of scope as evaluation targets, though usable as generic corpora.
6. **Memory is the differentiator.** Compounding cross-session memory is Memoria's core thesis, so memory/belief benchmarks are first-class. (This cluster is citation-disconnected from the scientific-research literature, so co-citation recommenders seeded on that literature never surface it — it must be found by name/capability.)

**Legend.** *Verdict:* **in-scope** = tests a core workflow directly; *partial* = relevant but narrowed (multimodal, system-not-benchmark, or DR-leaning). *Repo:* verified public code/data repo; "—" = none found or not verified here. *Mode* (how to use it): **run** = run the harness as-is for a number; **borrow** = adopt its metric/task into `vault-eval/`, don't run the leaderboard; **validate** = design/positioning evidence, cite don't run. Some support more than one; the listed mode is the recommended primary.

## Workflow-step categories

### 1. Find (`find`) — reasoning-intensive & temporal retrieval

Spans keyword/semantic search through reasoning-heavy and time-aware retrieval.

| Benchmark | arXiv | What it measures | Verdict | Repo | Mode |
|---|---|---|---|---|---|
| LitSearch | [2407.18940](https://arxiv.org/abs/2407.18940) | Scientific literature search (keyword/semantic) | in-scope | — | run |
| BRIGHT | [2407.12883](https://arxiv.org/abs/2407.12883) | Reasoning-intensive retrieval; SOTA retrievers ~18 nDCG@10 | in-scope | [xlang-ai/BRIGHT](https://github.com/xlang-ai/BRIGHT) | run |
| TEMPO | [2601.09523](https://arxiv.org/abs/2601.09523) | Temporal reasoning retrieval; tracking knowledge evolution | in-scope | [tempo-bench/Tempo](https://github.com/tempo-bench/Tempo) | borrow (Temporal Coverage@k) |
| AutoResearchBench | [2604.25256](https://arxiv.org/abs/2604.25256) | Complex scientific literature discovery by agents | in-scope | — | borrow (Wide-Research coverage) |
| MRMR | [2510.09510](https://arxiv.org/abs/2510.09510) | Reasoning-intensive retrieval w/ explicit Contradiction Retrieval | partial (multimodal) | data: [HF](https://huggingface.co/datasets/MRMRbenchmark) | borrow (Contradiction Retrieval) |
| Survey of Reasoning-Intensive Retrieval | [2605.00063](https://arxiv.org/abs/2605.00063) | Survey framing the RIR/BRIGHT cluster | partial (survey) | — | validate |

### 2. Ingest (`ingest`) — capture & document parsing

Bringing a source into the vault: parse the PDF, extract metadata and structure. Mostly deterministic tooling in Memoria (Zotero + Better BibTeX + PDF-plus), so it's lightly benchmarked — but extraction *fidelity* is a real, measurable capability.

| Benchmark | arXiv | What it measures | Verdict | Repo | Mode |
|---|---|---|---|---|---|
| DocBench | [2407.10701](https://arxiv.org/abs/2407.10701) | Raw file → QA: file parsing, metadata extraction, long-context reading | partial (reading-system eval; Memoria leans on plugins) | — | run |

### 3. Classify & promote (`classify` / `promote`) — classification & knowledge organization

| Benchmark | arXiv | What it measures | Verdict | Repo | Mode |
|---|---|---|---|---|---|
| ResearchArena | [2406.10291](https://arxiv.org/abs/2406.10291) | Collecting + organizing information as a researcher | in-scope | — | run |
| Automating Categorization of Scientific Texts | [2604.23430](https://arxiv.org/abs/2604.23430) | In-context categorization of scientific texts | in-scope | — | borrow (coarse-reliable/fine-hard finding) |
| Automated Ontology Generation | [2604.23090](https://arxiv.org/abs/2604.23090) | Building typed structure/ontology from unstructured text | partial (system) | — | validate |

### 4. Distill (`distill`) — literature distillation & understanding

| Benchmark | arXiv | What it measures | Verdict | Repo | Mode |
|---|---|---|---|---|---|
| SciLitLLM | [2408.15545](https://arxiv.org/abs/2408.15545) | Adapting LLMs for scientific-literature understanding | in-scope | — | run |
| Closed-Loop Literature Summarization | [2604.01452](https://arxiv.org/abs/2604.01452) | Human-LLM collaborative summarization | partial (system) | — | validate |

### 5. Frame & discuss (`frame` / `discuss`) — question framing & clarification

| Benchmark | arXiv | What it measures | Verdict | Repo | Mode |
|---|---|---|---|---|---|
| SCICONVBENCH | [2605.18630](https://arxiv.org/abs/2605.18630) | Multi-turn clarification for task formulation | partial | — | run |

*Thinly covered — note this as a benchmark gap for the `frame`/`discuss` surface.*

### 6. Query & assess (`query` / `assess`) — corpus QA & multi-document reasoning

| Benchmark | arXiv | What it measures | Verdict | Repo | Mode |
|---|---|---|---|---|---|
| PaperQA / LitQA | [2312.07559](https://arxiv.org/abs/2312.07559) | Retrieval-augmented QA over scientific papers | in-scope | — | run |
| KnowledgeBerg | [2604.17621](https://arxiv.org/abs/2604.17621) | Systematic knowledge coverage + compositional reasoning over a bounded set | in-scope (coverage) | — | borrow (coverage@k) |
| PaperMind | [2604.21304](https://arxiv.org/abs/2604.21304) | Agentic reasoning + critique over scientific papers | partial (multimodal) | — | run |
| RAGScholar & DBLP-QA | — | Source-attributed scientific QA (also touches `verify`) | in-scope | — | borrow |
| GraphWalker | [2603.28533](https://arxiv.org/abs/2603.28533) | Agentic KG-QA → querying a typed-relation graph | partial | — | borrow (graph-traversal method) |
| EpiBench | [2604.05557](https://arxiv.org/abs/2604.05557) | Multi-turn workflow: search → consult figures/tables → integrate evidence | partial (multimodal) | — | run |
| PaperScope | [2604.11307](https://arxiv.org/abs/2604.11307) | Multi-doc scientific QA across massive paper sets | partial (DR-leaning) | — | validate |

### 7. Code (`code`) — data-driven discovery, Coder lane [bounded]

In-scope only for the Coder lane, where Chen 2026's three preconditions hold (scalar criteria, reversible changes). Not a license for autonomous synthesis elsewhere.

| Benchmark | arXiv | What it measures | Verdict | Repo | Mode |
|---|---|---|---|---|---|
| ScienceAgentBench | [2410.05080](https://arxiv.org/abs/2410.05080) | Language agents on data-driven scientific tasks | partial (Coder lane) | — | run |
| DiscoveryBench | [2407.01725](https://arxiv.org/abs/2407.01725) | Data-driven discovery with LLMs | partial (Coder lane) | — | run |
| MASSW | [2406.06357](https://arxiv.org/abs/2406.06357) | AI-assisted scientific-workflow tasks | partial (Coder lane) | — | borrow (5-aspect note schema) |
| D3-Gym | [2604.27977](https://arxiv.org/abs/2604.27977) | Verifiable environments for data-driven discovery | partial (Coder lane) | — | run |

### 8. Verify (`verify`) — citation & attribution faithfulness

Memoria's `verify` is post-hoc citation by design; these stress that exact mode.

| Benchmark | arXiv | What it measures | Verdict | Repo | Mode |
|---|---|---|---|---|---|
| CiteME | [2407.12861](https://arxiv.org/abs/2407.12861) | Can LLMs attribute a claim to the correct paper | in-scope | — | run |
| CiteGuard | [2510.17853](https://arxiv.org/abs/2510.17853) | Retrieval-aware citation attribution; extends CiteME | in-scope | [KathCYM/CiteGuard](https://github.com/KathCYM/CiteGuard) | run |
| Generation-Time vs Post-hoc Citation | [2509.21557](https://arxiv.org/abs/2509.21557) | P-Cite (post-hoc) vs G-Cite; recommends P-Cite for high-stakes | in-scope (validates `verify`) | anon. 4open.science | validate |
| Correctness ≠ Faithfulness in RAG Attributions | [2412.18004](https://arxiv.org/abs/2412.18004) | "Post-rationalization": cited source looks supporting but unused | in-scope | — | borrow (NLI support check) |
| Citation Failure / CITECONTROL | [2510.20303](https://arxiv.org/abs/2510.20303) | When models fail to cite complete evidence | partial | [UKPLab/arxiv2025-citation-failure](https://github.com/UKPLab/arxiv2025-citation-failure) | borrow (completeness) |
| Source or It Didn't Happen | [2605.08583](https://arxiv.org/abs/2605.08583) | Multi-agent citation-hallucination detection | in-scope | — | run |
| BibTeX Citation Hallucinations | [2604.03159](https://arxiv.org/abs/2604.03159) | BibTeX field-level fabrication in publishing agents | in-scope | — | validate (deterministic-ingest) |
| The need for verification in AI-driven discovery | [2509.01398](https://arxiv.org/abs/2509.01398) | Position: verification as a first-class step | partial (position) | — | validate |

### 9. Write & revise (`write` / `revise`) — grounded drafting & revision

Memoria's Writer drafts and revises prose from claim notes, human-gated. The in-scope angle is **faithfulness/attribution-scored** generation — *not* the novelty-scored autonomous paper-writing benchmarks (out of scope, principle 3).

| Benchmark | arXiv | What it measures | Verdict | Repo | Mode |
|---|---|---|---|---|---|
| ALCE | [2305.14627](https://arxiv.org/abs/2305.14627) | Generate long-form answers with inline citations; fluency / correctness / citation quality | in-scope (closest fit) | — | run |
| CiteBench | [2212.09577](https://arxiv.org/abs/2212.09577) | Scientific citation-text generation — draft citing text grounded in papers-to-cite | in-scope | [UKPLab/citebench](https://github.com/UKPLab/citebench) | run |
| ExpertQA | [2309.07852](https://arxiv.org/abs/2309.07852) | Expert-curated long-form answers with verified attributions; experts also improve responses | in-scope | — | run |
| EditEval | [2209.13331](https://arxiv.org/abs/2209.13331) | Instruction-based text improvement (cohesion, updating outdated info, paraphrase) | in-scope (`revise`) | — | run |
| IteraTeR | [2203.03802](https://arxiv.org/abs/2203.03802) | Iterative text revision with edit-intention annotations | in-scope (`revise`) | — | borrow (edit-intention logging) |

### 10. Lint (`lint`) — belief maintenance over evolving / contradictory information

Maps to the contradictions dashboard, drift-watch, and `lint`.

| Benchmark | arXiv | What it measures | Verdict | Repo | Mode |
|---|---|---|---|---|---|
| ClawArena | [2604.04202](https://arxiv.org/abs/2604.04202) | Belief revision + multi-source conflict + implicit personalization for persistent assistants | in-scope (closest single fit) | [aiming-lab/ClawArena](https://github.com/aiming-lab/ClawArena) | borrow (CRS + scenario design) |

### Steps with no benchmark category

Four workflow steps are intentionally uncovered — deterministic bookkeeping, not capabilities a benchmark measures (the same "bookkeeping, not intelligence" logic that scopes this doc):

- **`zotero-capture`** — pulling references via Zotero + Better BibTeX.
- **`archive`** — moving stale notes to an archive folder (a state transition).
- **`export`** — rendering vault content to an output format.
- **`refactor`** — restructuring notes/links (mechanical maintenance; overlaps `lint`).

## Cross-cutting capabilities

Not pipeline steps — substrates or properties every workflow depends on: the **memory** it reads and writes, the **tool-call layer** it executes through, and the **permission/safety envelope** it operates within. Memory is Memoria's differentiator (and historically the least-covered); the other two are load-bearing because Memoria is entirely RPC-driven and ingests untrusted external content.

### Long-term agent memory & forgetting (memory tiers)

Maps to Memoria's memory tiers — cross-session recall (session search), knowledge updates, selective forgetting.

| Benchmark | arXiv | What it measures | Verdict | Repo | Mode |
|---|---|---|---|---|---|
| LongMemEval | [2410.10813](https://arxiv.org/abs/2410.10813) | Info extraction, multi-session reasoning, temporal reasoning, knowledge updates, abstention | in-scope | [xiaowu0162/LongMemEval](https://github.com/xiaowu0162/LongMemEval) | run |
| LoCoMo | [2402.17753](https://arxiv.org/abs/2402.17753) | Very long-term conversation (35 sessions): QA + event summarization | in-scope | [snap-research/locomo](https://github.com/snap-research/locomo) | run |
| MemoryAgentBench | [2507.05257](https://arxiv.org/abs/2507.05257) | Accurate retrieval, test-time learning, long-range understanding, selective forgetting | in-scope | [HUST-AI-HYZ/MemoryAgentBench](https://github.com/HUST-AI-HYZ/MemoryAgentBench) | run |
| Memora | [2604.20006](https://arxiv.org/abs/2604.20006) | Weeks-to-months memory; FAMA metric penalizes reliance on obsolete/invalidated memory | in-scope | [geniesinc/Memora](https://github.com/geniesinc/Memora) | borrow (FAMA) |
| Externalization in LLM Agents (survey) | [2604.08224](https://arxiv.org/abs/2604.08224) | Framework: memory/skills/protocols/harness externalization | partial (framing) | — | validate |

### Tool use & RPC reliability

Every workflow executes as tool calls — RPC to the Obsidian REST API (`27124`), the Hermes API (`8642`), and MCP. Unreliable function-calling breaks every lane at once, so this is the execution substrate beneath the whole pipeline.

| Benchmark | arXiv | What it measures | Verdict | Repo | Mode |
|---|---|---|---|---|---|
| τ-bench (tau-bench) | [2406.12045](https://arxiv.org/abs/2406.12045) | Multi-turn tool-agent-user interaction + policy-guideline adherence; `pass^k` reliability over repeated trials | in-scope (closest fit) | [sierra-research/tau-bench](https://github.com/sierra-research/tau-bench) | run |
| ToolLLM / ToolBench | [2307.16789](https://arxiv.org/abs/2307.16789) | Multi-step planning over 16k+ real-world APIs (ToolEval) | in-scope | — | run |
| API-Bank | [2304.08244](https://arxiv.org/abs/2304.08244) | Plan / retrieve / call APIs across tool-use dialogues | in-scope | — | run |
| On the Robustness of Agentic Function Calling | [2504.00914](https://arxiv.org/abs/2504.00914) | FC stability under query paraphrase + toolkit expansion (BFCL-based) | in-scope | — | borrow (narrow-lane finding) |
| ToolRet | [2503.01763](https://arxiv.org/abs/2503.01763) | Retrieving the right tool from a large toolset | partial (retrieval facet) | — | borrow (tool-selection finding) |

*BFCL (Berkeley Function-Calling Leaderboard) is the de-facto function-calling leaderboard but ships as a live leaderboard, not a standalone arXiv paper — track it directly, not via citation.*

### Agent safety: permission adherence & prompt-injection

Memoria *ingests untrusted external PDFs and then acts on them* — a textbook indirect-prompt-injection surface — while the Policy MCP confines every profile to its lane and allowed paths. These stress whether the agent stays in-bounds when tool data or ingested content turns adversarial.

| Benchmark | arXiv | What it measures | Verdict | Repo | Mode |
|---|---|---|---|---|---|
| AgentDojo | [2406.13352](https://arxiv.org/abs/2406.13352) | Prompt-injection attacks/defenses for agents executing tools over untrusted data | in-scope (closest fit) | [ethz-spylab/agentdojo](https://github.com/ethz-spylab/agentdojo) | run |
| InjecAgent | [2403.02691](https://arxiv.org/abs/2403.02691) | Indirect prompt injection in tool-integrated agents (user harm + data exfiltration) | in-scope | [uiuc-kang-lab/InjecAgent](https://github.com/uiuc-kang-lab/InjecAgent) | run |
| ToolEmu | [2309.15817](https://arxiv.org/abs/2309.15817) | LM-emulated sandbox surfacing high-stakes agent failures without manual setup | in-scope | — | run |
| AgentHarm | [2410.09024](https://arxiv.org/abs/2410.09024) | Refusal + robustness to overtly malicious agent tasks (jailbreaks) | partial (harmful-use; less central for single-user) | data: [HF](https://huggingface.co/datasets/ai-safety-institute/AgentHarm) | validate |

---

## Out-of-scope categories

Each is excluded by a numbered scoping principle above. Listed so the doc actively resists scope creep.

| Excluded category | Principle | Why | Examples |
|---|---|---|---|
| Autonomous scientist / end-to-end discovery | 3 | Scores unattended idea→experiment→paper; Memoria has a blocking human gate | AI Scientist v1/v2, Agent Laboratory, CORAL, PARNESS, AI-Researcher, AlphaLab, EvoMaster, ResearchEVO, Sibyl-AutoResearch, MLReplicate |
| Hypothesis & idea generation; novelty scoring | 3 | Memoria refuses autonomous synthesis and novelty-as-stopping-criterion | SciMON, ResearchAgent, Chain-of-Ideas, FlowPIE, CrossTrace, NovBench, Axiomatic Novelty Metrics, More Than Can Be Said |
| Model-weight knowledge editing | 4 | Edits parameters, not files; cite as contrast, don't run | CodeUpdateArena, EVK-Bench, "perplexing knowledge" (HierarchyData) |
| Deep-Research report generation | 2 | One-shot query→report; Memoria is corpus-curating and durable | DR³-Eval, DataSTORM, Self-Optimizing multi-agent Deep Research |
| Domain-specific science | 5 | Tests domain expertise, not PKM workflow (usable only as a generic corpus) | protein-design bench, PolyReal, ClimAgent, Re²Math, RMA, QED, SCOPE, BAGEL, MHGraphBench, COMPOSITE-Stem |
| Mislabeled (tests a different task) | 1 | Title suggests relevance but the task is something else | AgentSearchBench (discovers *agents* for a task, not literature) |

---

## Suggested minimal suite

One benchmark per Memoria surface, no autonomous-scientist assumptions imported:

1. **Memory / drift** → LongMemEval + Memora (FAMA) + ClawArena
2. **Retrieval** → LitSearch + BRIGHT
3. **Citation / verify** → CiteME + CiteGuard
4. **Organize** → ResearchArena
5. **Corpus QA** → PaperQA / LitQA
6. **Tool use & safety** → τ-bench + AgentDojo
7. **Draft & revise** → ALCE + EditEval
