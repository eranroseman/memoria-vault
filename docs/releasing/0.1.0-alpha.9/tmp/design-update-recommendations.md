# Memoria design-update recommendations — alpha.9

_Working artifact for the 0.1.0-alpha.9 checkpoint. Derived from the full literature review of **401 papers** in `_papers/` (synthesis: `_papers/REVIEW-SUMMARY.md`; per-paper verdicts: `_notes/paper-review-verdicts.json` — 162 adopt / 216 borrow ideas across 378 keeper papers). Decisions land in ADRs; this doc proposes them and is deleted before the release closes (AGENTS.md)._

## How to read this

The review found the frontier literature largely *re-derives* Memoria's design. **Caveat, read §0 first:** the corpus is the PI's own curated reading and the original review used a confirm-only vocabulary, so "re-derived" is partly an artifact of how it was run. §0 holds the disconfirmations and tensions that confirmatory framing hid; treat them as load-bearing, not appendix.

Every recommendation is tagged with its ADR disposition:

- **Validate** — a current bet is confirmed; record the empirical backing, no design change.
- **Amend** — sharpen an existing ADR with a specific mechanism the literature establishes.
- **Retire** — a current bet the literature argues *against*; replace it (see §0).
- **Tension** — two recommendations or a recommendation and a current bet pull against each other; unresolved until called out.
- **New** — a net-new capability that needs its own ADR (or a deferred ADR moved to active).

Each item gives **What → Why (papers) → ADR disposition**. Citations are short-form; full entries are in the review and `_papers/Exported Items.bib`.

---

## 0. Read this before §1 — problem, disconfirmations, tensions, budgets

**Content scope.** Memoria's primary content is academic papers (Zotero backbone, ADR-05/06/99) *plus* the PI's own claim/fleeting/project notes. Items below tagged **[paper-only]** assume a DOI + citation graph and do **not** apply to non-paper content: §3.3 primary-vs-review weighting, §4.4 citation-intent vocabularies. Everything else is content-agnostic.

**Current-state problem (need-push, not just literature-pull).** This doc is research-derived; the build order in §1 is *not* validated against observed alpha.9 pain. **Action:** before committing §1, write a one-page baseline of what the gate / contradictions / retrieval actually get wrong today, and re-rank against it. Until then, treat §1 as candidate moves, not a committed sequence.

**Where the literature argues against us (the confirm-only review hid these):**

- **Retire embedding cosine as the arbiter of "same / contradicts."** §3.1 is not an Amend — it says a current bet (cosine for contradiction/dedup/supersession) *actively fails* on negation and reasoning-relevance (BRIGHT). Re-tagged **Retire**.
- The disposition vocabulary was originally Validate/Amend/New, so nothing *could* land as a refutation. A 401-paper sweep with zero load-bearing disconfirmations is a method artifact; this section is the correction, and it is not exhaustive — a real §0 grows as the design is stress-tested.

**Open tensions — unresolved, do not paper over (Tension):**

1. **Compute vs. cost.** §3.6 (per-aspect prompts × 5–10 self-consistency samples ≈ 25–50 local calls/doc) is the largest compute line, not "free." It is a different axis from §5's ~6 *tool*-call budget. **Action:** add an explicit ingest-compute budget (calls/doc, nightly wall-clock) and stop calling self-consistency free.
2. **Supersession can silently suppress.** §3.4's retrieval filter, driven by a fallible meaning-changed classifier, can hide *correct* claims — the forgetting failure it set out to fix. The append-only trace keeps it auditable, but **apply §6's "expose what was down-ranked" to the supersession filter too.**
3. **Verbatim warrant vs. normalized claim.** §3.2 substring-grounds the **warrant = verbatim source span**; §3.1/§4.3 normalize the **claim text**. These are *different fields* (Knows/FEVER: `evidence_sentences` ≠ `claim_text`) — match the quote, never the normalized claim. Resolved by stating the separation; flagged here so no one re-collapses them.
4. **Frozen encoder buys little.** Open-question #5's "freeze the doc encoder so the index never re-embeds" is undercut by §4.1 indexing *claims*, which change as engines improve. Keep the freeze only for encoder-version decoupling; drop the "never re-embeds" rationale.

**Single PI-supervision budget (hard constraint, nothing currently models it).** Memoria is one human; co-PI is never required. These all draw on the *same* attention: NLI abstain-threshold calibration, POTENTIAL-middle review, confidently-novel escalation, warrant-check failures, judge-vs-PI validation, exemplar corrections, lesson distillation, schema-migration spot-checks. **Action:** set one annual label ceiling and make every §3–§5 mechanism draw against it. Lever: most of these can be *one* PI gate action emitting many signals (a single accept/reject resolves POTENTIAL **and** feeds the exemplar store **and** validates the judge **and** nudges the threshold) — design for one-action-many-signals, and model gate throughput, not just label count.

**Benchmark numbers are external, not in-domain.** Every point estimate in §3–§6 (nDCG deltas, %-closed-with-no-LLM, override rates, token savings) is one paper's setup. The *direction* is multiply-sourced and survives; the *digits* must be re-measured on Memoria's vault/model before they drive a threshold. Treat them as illustrative.

**Spike gate (do before ordering §1).** §1's #1 item (the NLI comparator) underpins §3.1/§3.3/§3.4/§5. Whether a usable NLI model fits 16 GB beside qwen2.5:7b — or the resident-LLM-as-verbalizer is accurate enough on the adversarial fixtures — is unanswered (open-question #1). **Run that spike first.** Fallback path (LLM-verbalizer) means a miss degrades rather than collapses the agenda, but the sequence below is not committed until the spike returns.

---

## 1. Recommended build sequence (executive)

Ordered by leverage, from the review's "what to build next" plus the cross-cutting synthesis. **Not committed** until the §0 NLI spike returns and the §0 current-state baseline is written. Detail follows in §3–§6.

1. **NLI/entailment comparator as a shared service** — one local entailment engine backing contradictions, dedup, supersession, and citation verification. *Highest leverage: it underpins three existing pillars at once.* (§3.1)
2. **Epistemic-status fields on every claim** — uncertainty flag + source-span provenance grade + source-type/evidence-strength. *Foundational and cheap; unblocks the NLI and gate work.* (§3.3)
3. **Model-free warrant checker at the gate** — substring + entity-type + year-order + opposite-edge + citekey-resolves. *Pure deterministic win, no model cost.* (§3.2)
4. **Supersession as a deterministic retrieval filter** over an append-only claim trace, with ISO temporal scope on claims. *Closes the universal memory failure (forgetting).* (§3.4)
5. **Expected-utility gate router (act / ask / drop)** replacing undifferentiated alerting. (§3.5)
6. **Constrained decoding + self-consistency in the engine layer.** *Highest-ROI engineering for faithful local extraction.* (§3.6)
7. **Retriever/scout on dense-over-claims + offline index enrichment + small-k reranker.** (§4.1)
8. **Engine certification harness** — state-based regression, pass^k, cost budgets, judges validated against PI labels. (§5)

---

## 2. Validated bets — record the backing, change nothing

These are confirmed by the corpus; the action is to cite the evidence in the relevant ADRs, not to change the design.

| Design bet | Confirming literature | ADRs validated |
|---|---|---|
| **Engines write, agents judge, PI approves** | Horvitz mixed-initiative (1999), Shneiderman–Maes (1997), Ackerman social-technical gap (2000), Bernstein/Soylent Find-Fix-Verify (2010), Cobbe verifiers (2021), Cornelio "verification is the bottleneck" (2025), Chen File-as-Bus (2026) | ADR-03, ADR-57, ADR-14, ADR-21, ADR-41, ADR-82 |
| **MCP-only agent sandbox (no file/terminal/code-exec, ever)** | Greshake indirect injection (2023), AgentDojo (2024), InjecAgent (2024), AI-Scientist self-modification incidents (Lu 2024), Perez & Ribeiro (2022) | ADR-32, ADR-46, ADR-28, ADR-27 |
| **Vault-as-memory / durable inspectable artifacts** | Chen File-as-Bus (2026), Zhou externalization (2026), PARNESS (2026), AgentRxiv (2025); ablations show removing durable state *collapses* multi-agent performance | ADR-01, ADR-46, ADR-23 |
| **Atomic claims store** | Five memory benchmarks: atomic-unit retrieval beats raw-log/summary retrieval | ADR-90, ADR-56, ADR-99 |
| **Deterministic ingest + cheap local model** | SciLitLLM (Qwen2.5, 2025), Schick & Schütze (2021), Agrawal clinical IE (2022); a 355M classifier beats GPT-4o zero-shot | ADR-30, ADR-108 |
| **Faithfulness over flash; local/cheap by choice** | Bender stochastic parrots (2021), Galactica (2022); efficiency as a first-class metric | ADR-22, ADR-24 |

---

## 3. Sharpenings — amend existing ADRs

The genuine "change X" recommendations. Each names the current design area and the specific mechanism to adopt.

### 3.1 Contradiction / supersession / dedup must run on NLI, never cosine — **Retire (cosine) + Amend ADR-09, ADR-10, ADR-94, ADR-38**

**What.** Stand up a single **local NLI/entailment comparator** as a shared MCP service and route contradictions, claim-supersession, record-linkage dedup, and the pre-file similarity gate through it. Use FEVER's tri-class verdict vocabulary **SUPPORTED / REFUTED / NOTENOUGHINFO**, and require every verdict to carry its **evidence sentence(s)**, not just a label. Default conservative with a **tunable abstain threshold**; route the uncertain middle (POTENTIAL) to the PI. Key dedup on canonical IDs.

**Why.** Plain embedding cosine is blind to negation and collapses (~59→~18 nDCG on BRIGHT) precisely on the reasoning-based, cross-paper relevance the argument graph exists to capture; high similarity routinely coexists with *flipped meaning* (BRIGHT/Wei 2026, Utama 2021). Frozen-NLI + MaxSAT resolves the globally consistent claim set in <20ms with no training (ConCoRD/Mitchell 2022); relation-as-NLI-hypothesis with entity-type constraints is training-free and makes "detect NO relation" — the dominant, hard case — explicit (Sainz 2021). The costly error is a false "duplicate/contradiction," so precision-first with abstention (CITETRACER, CiteGuard).

**Concrete.** (a) Pick a local NLI model sized for the 16GB box (see §7 open question). (b) Verdict schema `{verdict, evidence_sentences[], score}`. (c) MaxSAT consistency pass over the claim graph to pinpoint flagged claims — surfaced to the gate, never an autonomous overwrite. (d) Adversarial **word-overlap-but-opposite-meaning** and **near-duplicate-but-distinct** fixtures with an explicit false-positive budget.

### 3.2 Model-free warrant checker as a hard gate invariant — **Amend ADR-03, ADR-57, ADR-79**

**What.** Before any claim or typed edge is written, a **deterministic, no-LLM checker** must pass: source-span **substring grounding** of the warrant quote, **entity-type** compatibility, **year-ordering**, **opposite-direction-edge** contradiction check, and **citekey resolves** in Zotero/vault. Structural validity is machine-checked; semantic correctness is deferred to agent/PI.

**Why.** Bare LLM judges err 16–46% on citation/claim calls and *post-rationalize* citations they didn't use (CiteGuard, Wallat 2024, CITETRACER); an injection fools the judge too, so deterministic state-based checks must do adjudication (AgentDojo). Intern-Atlas and PubTator build exactly this verbatim-warrant + deterministic-validator pipeline (Wu 2026, Wei 2024). CITETRACER closes 61.7% of cases with **no LLM call**.

**Concrete.** Add the checker to the structural review gate as a fail-fast lint stage; reject any relation/contradiction lacking correct warrant sentences. Add a **causal-faithfulness counterfactual** offline test: inject a claim's span into a decoy source; if the engine re-cites the decoy, mark the attribution low-confidence (Wallat 2024).

### 3.3 Epistemic status as first-class, auditable claim data — **Amend ADR-56, ADR-08, ADR-50**

**What.** Every atomic claim (and relation) carries: an **uncertainty flag**, a **source-span provenance grade** (complete / partial / broken), **two-axis confidence** (claim_strength vs extraction_fidelity), and **source-document-type** (review vs primary vs preprint) + **evidence-strength**. Contradiction/supersession privilege **primary evidence over echoed consensus**.

**Why.** LM fluency is not knowledge (Bender 2021); reverse-inferred labels need reliability/specificity discipline (Barrett). Self-consistency disagreement *becomes* the uncertainty flag (Wang 2023) — cheap as a by-product of the §3.6 sampling already being paid for, **not free** (see §0 tension 1). Knows (Yu 2026) ships this exact two-axis-confidence + replaces-chain schema as external validation. **Version-pin epistemic metadata:** the uncertainty/confidence fields are model-specific, so stamp each with the producing model + prompt version — a qwen2.5→qwen3 swap silently shifts every value otherwise. Tagging source-type and weighting primary evidence prevents a review restatement from outvoting the study it cites (Schwappach 2025).

**Concrete.** Extend the claim/source-note frontmatter schema; populate uncertainty from self-consistency sample-disagreement at ingest; add a `source_anchor` (page/section/figure) per claim.

### 3.4 Promote supersession from dashboard to deterministic retrieval filter; make time a first-class field — **Amend ADR-10, ADR-09, ADR-92, ADR-65**

**What.** Supersession becomes a **deterministic filter applied during retrieval** over an **append-only claim trace** (singly-linked `replaces` chain + `record_status: superseded` + `stale_after`), not just a dashboard view. Stamp every claim with **ISO temporal scope + tense + confidence**. Add **cross-period coverage metrics** (Temporal Coverage@k) to the scout and **abstain when retrieved evidence is time-mismatched**.

**Why.** Forgetting — not recall — is the universal memory failure: every memory agent silently surfaces superseded facts and degrades over horizon. Temporally-incomplete retrieval *actively harms* output (TEMPO/Abdallah 2026: no-retrieval beat all RAG). A newer in-context claim overrides stale belief ~85% of the time (Si), so feed superseding claims into the prompt and flag the conflict rather than trusting memory.

**Concrete.** Append-then-compete discipline — never overwrite an approved claim; a candidate successor must re-pass the gate (Gottweis 2025, PARNESS). A **meaning-changed vs cosmetic edit** classifier on re-ingest decides when to supersede (Du 2022). Test with a **forgetting-aware metric**.

### 3.5 Make the gate an explicit expected-utility act / ask / drop router — **Amend ADR-70, ADR-81, ADR-41, ADR-03**

**What.** Replace any undifferentiated alerting with a **cost/benefit router**: auto-apply low-risk/high-confidence items, **batch-and-rank** ambiguous items to the gate, drop the rest. Route **confidently-novel** items to review, not just low-confidence ones.

**Why.** Horvitz's mixed-initiative expected-utility math is the formal backbone (1999); HCI is unanimous that an alert firehose causes rubber-stamp fatigue (Chordia 2023, Friedman 2013, Brown 2007 glanceable digests). Confidently-wrong novel cases also need escalation (Alkhatib 2019). HITL evidence: targeted high-leverage approval beats both full autonomy and step-by-step approval (AutoResearchClaw 2026).

**Concrete.** Probability bands → {drop, ask-at-gate, auto-write}; a cheap pre-gate classifier guards expensive extraction (maps to ADR-38). Surface **capability + expected error rate + why** on every engine output (Amershi G1/G2/G11).

### 3.6 Constrained decoding + self-consistency as the engine-layer contract — **Amend ADR-30, ADR-42, ADR-90, ADR-99**

**What.** Standardize every ingest engine as **decomposed, per-aspect, schema-constrained prompts + a tiny deterministic resolver**, wrapped in **self-consistency sampling** (5–10 paths, unweighted majority vote) whose disagreement populates the uncertainty flag. temperature=0 for extraction; closed label sets presented explicitly (OPTIONS suffix).

**Why.** The brittleness of cheap local models is structured-output adherence, not capability — constrain the output, not the model (Schick & Schütze 2021, SciLitLLM 2025). Guided-format decoding makes output valid by construction in one local pass (Agrawal 2022, LMQL/Beurer-Kellner 2023, Shin 2021). Adopt the **MASSW five-aspect schema** with mandatory "N/A" for absent aspects verbatim (Zhang 2024). Per-aspect prompts make each slot independently gate-checkable.

**Concrete.** One targeted prompt per aspect over one mega-prompt; gate-existence-before-extraction chaining to kill hallucinated claims; counterfactual perturbation to confirm the extractor tracks text, not priors.

---

## 4. New capabilities to add — new or activated ADRs

Adopt-grade ideas not yet in the design.

### 4.1 Retriever/scout: instruction-tuned dense-over-claims + offline enrichment + small-k reranker — **New / extend ADR-37, ADR-65, ADR-92**

**What.** Default the retriever/scout to an **instruction-tuned dense encoder** (GritLM/E5/Instructor class) indexing **title + abstract + extracted atomic claims, not whole PDFs**, with a **BM25 lexical fallback**. Add an **LLM reasoning-trace query expansion** front-end and a **small-k LLM-judge reranker** ("context library"). Shift LLM cost **offline**: at ingest, attach "hypothetical questions this claim answers" as searchable metadata.

**Why.** Retrieval quality — not model size or agentic search — drives grounded output; one-line BM25/title baselines beat long agentic deliberation (ResearchArena/Kang 2024, BRIGHT/Su 2025). Index compact units, PQ-compress to fit 16GB (LitSearch/Ajith 2024). Off-the-shelf MS-MARCO cross-encoders *hurt* on reasoning relevance — keep k small and validate before adding (Wei 2026). Cap aggregated evidence at ~3 docs for qwen2.5:7b (Neekhra 2026).

### 4.2 Cheap, non-LLM methods ahead of every model pass — **New / extend ADR-93, ADR-94, ADR-33**

**What.** **MinHash-LSH / n-gram** near-duplicate detection; **PMI / class-TF-IDF** n-gram extraction for keyphrase tags and cluster labels; **per-aspect embeddings + coding-then-clustering** (UMAP→HDBSCAN→centroid-nearest-code labels) for the corpus map; **random-walk-with-restart** over the typed graph for topological discovery with path-based "why retrieved" explanations.

**Why.** Most of dedup, keyphrase, and clustering needs no LLM at all (Brown 2020, Diao 2023, Hämäläinen 2023, Qiao/SciAtlas 2026). Deterministic pre-filters belong ahead of every expensive LLM pass — the "engines filter cheaply, agents judge" gate.

### 4.3 Two-stage normalize/dedup: retrieve-shortlist → local-LLM-pick — **New / extend ADR-94**

**What.** An embedding retriever proposes ~√N candidate canonical entities; a small local LLM under the gate picks the match. Entity canonicalization is the cross-note **join key** (char-3-gram + ANN, type-by-type, coarse-to-fine).

**Why.** LLMs reliably mint near-duplicate entities, so dedup must be keyed on canonical IDs; the shortlist-then-pick pattern keeps the LLM call small (Berkowitz/RAGnorm, SciLinker, PubTator).

### 4.4 Typed-relation controlled vocabularies + constructive-necessity test — **New / extend ADR-98, ADR-52, ADR-79**

**What.** Replace a generic "cites" edge with **citation-intent** (Background / CompareOrContrast / Extends / Uses / Motivation) and **functional-role** (Core Method, Conceptual Framework, Data Source, Eval Protocol) taxonomies, classifiable by a 7B model on ingest. Gate dependency edges by a **constructive-necessity test** ("if I had to build this tomorrow, what would I still need?") and record an explicit **unmapped / NONE** outcome — which simultaneously surfaces a research gap for discovery.

**Why.** Reasoning-relevance is multi-typed; recording NONE rather than forcing a citation prevents over-linking and feeds the discovery loop (SciPaths, CiteBench, Wei 2026). Treat the schema as a deliberate lossy KR whose **constraints ARE the representation** (Davis).

### 4.5 Editable exemplar store for personalization — no training — **New / extend ADR-35, ADR-23**

**What.** A FAISS/ANN datastore of **PI-confirmed exemplars** (relation/claim/aspect decisions) so a gate correction becomes a new key-value that immediately shifts future extractions. Plus **time-decayed, role-scoped "lesson" overlays** distilled from recurring PI accept/reject patterns, injected into compiled profile prompts.

**Why.** Personalize through an editable store, not weights — keeps personalization inspectable, auditable, revertible, and matches the no-training constraint (RetrievalRE/Chen 2023, Gottweis 2025). Explicitly **reject** weight-internalized preferences (NanoResearch's label-free policy learning) — the co-trained-reviewer failure mode.

### 4.6 Negative-results / "what never worked" store — **New / extend ADR-100, ADR-61/95**

**What.** Record rejected directions and dead ends so the discovery loop and triage never re-surface them; track a per-PI **seen/dismissed** set (gray out visited, push toward unexplored).

**Why.** Narrative publication discards failure knowledge — the same gap the vault has (CORAL/Qu 2026, ARA, Faste 2013). Complements supersession/contradictions.

---

## 5. Evaluation & instrumentation — **Amend ADR-62, ADR-104/105/106, ADR-29, ADR-80**

**What.**
- **State-based evaluation + pass^k consistency** — judge the resulting vault state vs an expected state (path-independent); certify that *all* k reruns succeed, not best-of-k (tau-bench 2024).
- **Groundedness as a gate metric** — NLI-entailment citation recall/precision over decomposed atomic sub-claims, validated against human judgment (ALCE/Gao 2023, κ≈0.70); a lexical span-overlap check is the cheap deterministic substitute.
- **Validate LLM-judges against the PI's own approve/reject labels** before trusting them; sample-3-and-average; treat the score as a triage signal, not certification.
- **Reward abstention** — score an "insufficient-evidence / choose-unknown" output as correct (DOCBENCH, BBQ, TEMPO).
- **Trivial-control baselines** (majority-class, always-accept-venue) so triage gains aren't distributional shortcuts; partition eval into "guessable from metadata" vs "needs content."
- **Bootstrap eval fixtures** by model-writing labeled examples (generate-then-discriminate), then PI-validating a sample (Perez 2022); synthesize via controlled mutation operators (paraphrase, negation, generalize/specialize) with round-trip diff audits (FEVER, CITETRACER).
- **Cost as a first-class metric** with a tool-call budget (~6 calls; ≥10 degrades via context dilution) (ScienceAgentBench 2025).

**Why.** Automatic surface metrics (BLEU/ROUGE/BERTScore) track human judgment only weakly; process- and abstention-level scoring catches "right answer, wrong reason" (EpiBench 2026, ExpertQA 2024). Every threshold/prompt/judge tuned on the PI's notes is **spent supervision** — freeze and version-pin, never report quality on the tuning set.

---

## 6. Surfaces — projection, inspector, dashboards — **Amend ADR-102/103, ADR-84, ADR-87, ADR-71, ADR-101**

**What.**
- **Render over native inspectable artifacts** (Obsidian markdown / JSON Canvas / static HTML) and **diff-re-project by stable key** (citekey / claim-id) so layout is preserved across re-projection (D³/Bostock 2011, Beaudouin-Lafon 2000).
- **Encode the single highest-priority signal preattentively** (contradiction status, uncertainty, supersession); precompute conjunctions ("contradicted AND stale") as their own mark; cap categorical color (Healey & Enns 2012, Fekete 2008).
- **Show evidence weight + dissent + a no-suggestion baseline, never a single persuasive rationale** — confident wrong outputs and tidy feature-explanations *actively harm* an expert (Jacobs 2021, Govers 2026). The contradictions dashboard surfaces support/contradict **counts with provenance**, not a tidy "X% agree."
- **Expose what the ranker down-ranked** so minority claims aren't silently suppressed.
- **Computational wear** — render the PI's own read/edit/revisit history as salience, feeding learning-to-rank triage (Hill 1992).
- **Token-tiered projection** — a statements-only projection keeps ~88% comprehension at ~93% fewer tokens; escalate to full evidence/text only on low confidence (Knows/Yu 2026).
- **Faceted navigation** as an Obsidian Base over typed metadata with live result counts before a filter is committed (Hearst 2009).

---

## 7. Open questions & risks

1. **Local NLI model selection (blocks §3.1).** Which entailment model fits the 16GB RTX 4060 Ti alongside qwen2.5:7b — a dedicated small NLI model (DeBERTa-MNLI class) vs prompting the resident LLM as an NLI verbalizer? Validate on the adversarial fixtures before committing. Ties to the test-env model split.
2. **Where evidence-strength / source-type metadata comes from at ingest (§3.3).** Zotero item-type gives review-vs-primary cheaply; evidence-strength may need a classifier or PI tagging.
3. **Migration of existing claims to the new schema fields (§3.3, §3.4).** Backfill uncertainty/temporal-scope/provenance-grade on already-filed claims — one-time engine pass with PI spot-check, or lazy-on-touch?
4. **NLI false-positive budget calibration (§3.1).** The abstain threshold trades over-linking against missed contradictions; needs the PI's own labels to set, and that is spent supervision.
5. **Index re-embedding cost (§4.1).** Freeze the doc encoder (query-side-only adaptation) so the vault index never needs re-embedding if a retriever is ever tuned (Atlas/Izacard 2022).

---

## 8. ADR worklist (proposed)

| Disposition | ADRs | Recommendation |
|---|---|---|
| Validate (cite backing) | 03, 57, 32, 46, 28, 27, 01, 30, 90 | §2 |
| Amend | 09, 10, 94, 38 | §3.1 NLI comparator |
| Amend | 03, 57, 79 | §3.2 warrant checker |
| Amend | 56, 08, 50 | §3.3 epistemic status |
| Amend | 10, 09, 92, 65 | §3.4 supersession filter + temporal |
| Amend | 70, 81, 41, 03 | §3.5 gate router |
| Amend | 30, 42, 90, 99 | §3.6 constrained decoding |
| New / extend | 37, 65, 92 | §4.1 retriever |
| New / extend | 93, 94, 33 | §4.2 non-LLM methods |
| New / extend | 94 | §4.3 normalize/dedup |
| New / extend | 98, 52, 79 | §4.4 relation vocabularies |
| New / extend | 35, 23 | §4.5 exemplar store |
| New / extend | 100, 61/95 | §4.6 negative-results store |
| Amend | 62, 104/105/106, 29, 80 | §5 evaluation |
| Amend | 102/103, 84, 87, 71, 101 | §6 surfaces |

---

## 9. Provenance

- **Source corpus:** 401 papers, `_papers/` (Zotero export `_papers/Exported Items.bib`).
- **Synthesis:** `_papers/REVIEW-SUMMARY.md` (executive summary, 9 cross-cutting themes, 11 category deep-dives).
- **Per-paper verdicts:** `_notes/paper-review-verdicts.json`.
- **Docs already wired to the review:** PR #784 (`docs/explanation/overview/intellectual-foundations.md`, `docs/explanation/rationale/why-pattern-provenance.md`, `docs/reference/bibliography.md`).
