# Memoria design-update recommendations — alpha.9

_Working artifact for the 0.1.0-alpha.9 checkpoint; deleted before the release closes (AGENTS.md). Decisions land in ADRs — this doc proposes them._

_Rewritten after the work below changed the picture. Provenance: a literature review of 401 papers (`_papers/REVIEW-SUMMARY.md`, verdicts in `_notes/paper-review-verdicts.json`), then an adversarial refutation pass (`_papers/REVIEW-REFUTATIONS.md`), then **on-box measurement** of the contested claims (`spike-nli-vs-cosine.py`, `probe-qwen-compliance.py`). Earlier confirmation-first framing is superseded by §0._

## How to read this

Three passes produced this doc, in increasing trust:

1. **Literature review** — confirmation-biased (the corpus is the PI's own curated reading, scored with a confirm-only vocabulary). It claimed the literature "re-derives" Memoria's design. Treat that claim with suspicion.
2. **Refutation pass** — attacked 14 load-bearing bets; **none survived intact**. The corpus endorses the *skeleton* (durable file state, verbatim warrants, batch surfacing, a *sparse* gate, deterministic external grounding, supersession-as-edge) and refutes most *strong claims layered on top*.
3. **On-box measurement** — the contested, testable claims, run against the actual RTX 4060 Ti + qwen2.5:7b + local NLI. Where a claim was measured, the measurement wins over both the literature and the refutation.

**Trust order: measured > refuted > literature-pull.** Every item carries a disposition (**Validate / Amend / Retire / Tension / New**) and, where relevant, a **status** (`measured ✓`, `refuted on-box`, `measured-partial`, `untested`). Citations are short-form; full entries in `_papers/Exported Items.bib`.

---

## 0. The state of play — read before §1

### 0a. What we measured on-box (highest confidence)

| Contested claim | Measured result | Verdict |
|---|---|---|
| Cosine arbitrates same/contradicts | 0/8 on word-overlap/opposite-meaning pairs (rates all 8 "same", 0.78–1.00) | **Blind spot confirmed** — retire cosine as the arbiter |
| NLI fixes it | 8/8 on the same trap; direction-stable; **<0.6 GB VRAM** | NLI clears the *easy* trap; HANS failure didn't materialize here |
| NLI is clean | On same-topic / **different-variable** pairs it **confidently fabricates contradictions at 0.94–1.00** (small 6/12, ANLI 8/12) | NLI alone is a false-contradiction generator; a confidence threshold can't filter it |
| Variable-match gate fixes that | Holistic LLM "same variable?" → **recall 1/6** (drops real contradictions). Decomposed (entity+attribute+direction) → **recall 4/6, FP dropped 6/7** | **Necessary, not sufficient**; bottleneck moves to direction/relationship extraction (negation, argument-order, value-conflict) |
| Frozen qwen2.5:7b ≈ 0% schema compliance (CrossTrace) | MASSW aspect extraction **6/6 clean** (Ollama `format=schema`); verbatim warrant quotes **90% (18/20)** | **Refuted on our tasks.** §3.6 confirmed; **QLoRA budget dropped**; §3.2's substring checker catches the 10% |
| NLI must fit beside qwen on 16 GB | <0.6 GB, and qwen is a test fixture not a co-resident | Fit was a phantom blocker — **dissolved** |

Measurement caveat that applies to all of the above: hand fixtures (~20–30 pairs) + abstract/intro text. These are **smoke tests that answer go/no-go, not benchmarks.** Re-run on real vault claims (`current-state-baseline.md`) before any threshold is trusted.

### 0b. What the literature refutes but we could NOT test here (warnings, need PI data)

These are the disconfirmations with no on-box probe — they require the PI's real vault/feedback, so they stand as **open risks, ranked by blast radius**:

1. **Human + machine ≯ machine — the gate's load-bearing premise may be false.** Jacobs 2021 (N=220): clinician+ML ≈ clinician-alone, both far below ML-alone, and a *wrong* recommendation dragged the human *below* their no-rec baseline. If this holds for Memoria, "PI approves" does not automatically improve correctness and the gate is theater. **This is the existential risk to the whole architecture and the first thing to measure once there is PI approve/reject data. ADR-03/57/24.**
2. **Atomic-as-stored-unit hurts QA** — the contextual round is the optimal retrieval unit, the atom an index over it (LongMemEval, Hu 2026). Needs a labeled retrieval set on the real vault.
3. **Durable graph memory underperforms BM25** on synthesis tasks (MemoryAgentBench). Needs the vault corpus to test.
4. **Automatic contradiction/supersession is the least-reliable memory capability** (~28% wrong flips, Mitchell 2022). The §3.1 gate test already shows the proposer is lossy; real proposer-precision needs vault data.
5. **Least-privilege ≠ security against poisoned papers** — the dominant threat is untrusted *data*, not code (Greshake, Debenedetti). Architectural, not benchmarkable; handled by naming the gate as an imperfect, itself-injectable integrity control.

### 0c. Binding constraints (apply to everything in §1–§6)

- **Content scope.** Primary content is academic papers (Zotero backbone, ADR-05/06/99) *plus* the PI's own claim/fleeting/project notes. Items tagged **[paper-only]** (§3.3 primary-vs-review weighting, §4.4 citation-intent) assume a DOI + citation graph and do **not** apply to non-paper notes. Everything else is content-agnostic.
- **Single PI-supervision budget.** Memoria is one human; co-PI is never required. NLI threshold calibration, POTENTIAL review, novelty escalation, warrant-check failures, judge validation, exemplar corrections, lesson distillation, schema-migration spot-checks all draw on the *same* attention. Set **one annual label ceiling** and make every mechanism draw against it. Lever: design for **one PI action emitting many signals** (a single accept/reject resolves POTENTIAL *and* feeds the exemplar store *and* validates the judge *and* nudges the threshold); model **gate throughput**, not just label count.
- **Need-push, not literature-pull.** §1's order is research-derived, **not** validated against observed alpha.9 pain. Fill `current-state-baseline.md` (gate false-approve / contradiction precision / retrieval recall on real runs) and re-rank against it before committing §1.
- **Benchmarks are external.** Every literature point estimate (nDCG deltas, %-no-LLM, override rates, token savings) is one paper's setup. The *direction* is multiply-sourced and survives; the *digits* must be re-measured in-domain.

---

## 1. What to do for alpha.9 — evidence-weighted, with a cut line

The original "8-item build sequence" was literature-leverage ordering. Re-weighted by what measurement and the PI-budget constraint now say:

**Ship (measured-green, cheap, foundational):**
1. **Constrained-decoding engine contract** (§3.6) — *measured 6/6*. Per-aspect schema-constrained prompts + a tiny resolver. Lowest risk, unblocks everything else.
2. **Model-free warrant checker at the gate** (§3.2) — *measured: 90% of qwen warrants are verbatim, the checker rejects the other 10%*. Pure deterministic, no model cost.
3. **Epistemic-status claim fields** (§3.3) — uncertainty flag + provenance grade + source-type. Cheap, and the precondition for §3.1's gate.

**Build with care (measured-partial):**
4. **NLI relationship verdict + decomposed variable-match gate** (§3.1) — *precision win, measured recall cost*. Propose-only; the hard part is faithful direction/relationship extraction, not the NLI verdict.

**Measure before you build (untested, highest stakes):**
5. **The Jacobs calibration check** (§3.5 / gate) — instrument "do PI-approved writes actually beat raw engine writes?" *before* investing more in the gate. If the answer is no, the architecture needs rethinking, not tuning.

**Defer past alpha.9** (literature-pull, not yet earned): the retriever overhaul (§4.1), the typed graph (now demoted — must beat a BM25+dense baseline before it earns space), the exemplar store (§4.5), the certification harness (§5) beyond the Jacobs check.

**Explicitly NOT doing for alpha.9:** QLoRA fine-tuning (refuted), ripping out cosine wholesale (keep it as a control), auto-applied contradiction/supersession links (propose-only until proposer precision is measured on real data).

---

## 2. Validated skeleton — backing holds; the strong form of four rows is contested (§0)

Cite the backing in the ADRs, but do **not** read this table as "no change needed" — the strong claim of each starred row was contested or refuted on-box.

| Design bet | Confirming literature | Status | ADRs |
|---|---|---|---|
| Engines write, agents judge, PI approves | Horvitz (1999), Shneiderman–Maes (1997), Ackerman (2000), Bernstein/Soylent (2010), Cobbe (2021), Cornelio (2025), Chen File-as-Bus (2026) | ⚠ strong form **untested & at risk** (Jacobs, §0b.1) | 03, 57, 14, 21, 41, 82 |
| MCP-only sandbox (no file/terminal/code-exec) | Greshake (2023), AgentDojo (2024), InjecAgent (2024), Lu (2024), Perez & Ribeiro (2022) | ⚠ necessary, **not sufficient** (data > code, §0b.5) | 32, 46, 28, 27 |
| Vault-as-memory / durable artifacts | Chen (2026), Zhou (2026), PARNESS (2026), AgentRxiv (2025) | ✓ validated | 01, 46, 23 |
| Atomic claims store | five memory benchmarks (atomic > raw-log) | ⚠ as *index*, not *stored unit* (§0b.2) | 90, 56, 99 |
| Deterministic ingest + cheap local model | SciLitLLM (2025), Schick & Schütze (2021), Agrawal (2022) | ✓ **measured-confirmed** (6/6 + 90%, §0a) | 30, 108 |
| Faithfulness over flash; local/cheap by choice | Bender (2021), Galactica (2022) | ✓ validated (and frozen-model now measured-sufficient) | 22, 24 |

---

## 3. Sharpenings — amend existing ADRs

### 3.1 Contradiction / dedup / supersession: retire cosine → NLI relationship-verdict + decomposed gate — **Retire (cosine) + Amend ADR-09, ADR-10, ADR-94, ADR-38** · status: measured-partial

**What.** A single **local NLI/entailment comparator** (FEVER tri-class SUPPORTED / REFUTED / NOTENOUGHINFO, every verdict carrying its evidence sentence) supplies the **relationship verdict only**. A contradiction/dedup edge additionally requires a **decomposed variable-match** — extract `(entity, attribute, direction)` as *separate* fields (§3.3) and confirm entity+attribute match with direction-conflict — **never a holistic LLM "same variable?" call**. Edges are **proposed, never auto-applied**; key dedup on canonical IDs.

**Why + what we measured.** Cosine is blind to negation (0/8 on the trap, §0a) — retire it as the arbiter, keep it only as a **control baseline**. NLI clears the easy trap (8/8) but **confidently mints false contradictions between merely-different claims** (0.94–1.00 on different-variable pairs), and a confidence threshold can't filter that — so the structured variable-match gate is a **precondition, not an enhancement**. The gate works: holistic recall 1/6 → decomposed 4/6, false-positives dropped 6/7. The residual losses (negation read as same-direction, argument-swap, same-attribute/different-value) are **relationship-extraction failures, not NLI failures** — that is now the hard part. Prefer the **ANLI/FEVER model** (`MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli`, better on neutral); `small` ties only on the easy trap; read `id2label` (label order differs across models — never hardcode).

**Concrete.** (a) ANLI/FEVER NLI under MCP, `<0.6 GB`. (b) Verdict `{verdict, evidence_sentences[], score}`, gated by decomposed variable-match before becoming an edge. (c) MaxSAT consistency pass over the *gated* edges only (ConCoRD/Mitchell 2022); surfaced to the gate, never auto-applied — track **proposer precision** first (least-reliable memory capability). (d) Keep both the HANS/trap and the different-variable **NEUTRAL** fixtures as regression tests; re-run on real claims before trusting the recall number.

### 3.2 Model-free warrant checker as a hard gate invariant — **Amend ADR-03, ADR-57, ADR-79** · status: measured ✓

**What.** Before any claim/edge is written, a **deterministic, no-LLM checker** passes: substring grounding of the verbatim warrant quote, entity-type compatibility, year-ordering, opposite-direction-edge check, and citekey resolves in Zotero/vault. Structural validity machine-checked; semantic correctness deferred to agent/PI.

**Why + measured.** Bare LLM judges err 16–46% on citation calls and post-rationalize citations (CiteGuard, Wallat 2024, CITETRACER); an injection fools the judge too, so deterministic checks must adjudicate (AgentDojo). **On-box: 90% of qwen2.5:7b warrant quotes are exact substrings — the checker passes those and rejects the other 10%, which is its whole job.** Note the field separation (a §0 tension, now resolved): the **warrant is the verbatim source span** (substring-checkable); the **claim text is normalized** (never substring-matched against source). Different fields (Knows/FEVER: `evidence_sentences` ≠ `claim_text`).

**Concrete.** Fail-fast lint stage at the gate; reject any edge lacking a correct warrant sentence. Add a causal-faithfulness counterfactual offline test (inject a span into a decoy source; if the engine re-cites it, mark low-confidence — Wallat 2024).

### 3.3 Epistemic status as first-class, auditable claim data — **Amend ADR-56, ADR-08, ADR-50**

**What.** Every claim (and relation) carries: uncertainty flag, source-span provenance grade (complete/partial/broken), two-axis confidence (claim_strength vs extraction_fidelity), source-document-type **[paper-only]** (review/primary/preprint) + evidence-strength, and a `source_anchor` (page/section/figure). Contradiction/supersession privilege primary evidence over echoed consensus.

**Why.** LM fluency is not knowledge (Bender 2021). Self-consistency disagreement can populate the uncertainty flag (Wang 2023) — but it is **not free** (it is the §3.6 sampling cost) and **not a confidence signal at 7B** (blind to stable fabrication), so use it **only on closed-label steps**. **Version-pin epistemic metadata** to the producing model + prompt — a qwen2.5→qwen3 swap silently shifts every value. The `(context, variables, relationship)` decomposition here is also what §3.1's gate consumes — build it once.

**Concrete.** Extend the claim/source-note frontmatter schema; populate uncertainty from closed-label self-consistency; backfill is an open question (§8).

### 3.4 Supersession as a deterministic retrieval filter; time as a first-class field — **Amend ADR-10, ADR-09, ADR-92, ADR-65**

**What.** Supersession becomes a deterministic filter over an **append-only** `replaces` chain (`record_status: superseded`, `stale_after`), with **ISO temporal scope + tense + confidence** on every claim and **Temporal Coverage@k** on the scout; abstain when retrieved evidence is time-mismatched.

**Why + caution.** Forgetting, not recall, is the universal memory failure; temporally-incomplete retrieval actively harms output (TEMPO/Abdallah 2026). **But the filter can silently suppress correct claims** if the meaning-changed classifier is wrong — so keep superseded claims **retrievable** (tagged "superseded by [[X]] on [date]"), penalize *stale-as-current reuse* rather than hard-excluding, and **expose what the filter dropped** (the §6 rule applies here too). Cross-period/trend queries need both the baseline and the current claim.

**Concrete.** Append-then-compete (a successor re-passes the gate); a meaning-changed-vs-cosmetic classifier on re-ingest (Du 2022); a forgetting-aware metric.

### 3.5 Expected-utility gate router — and instrument the Jacobs question first — **Amend ADR-70, ADR-81, ADR-41, ADR-03**

**What.** Replace undifferentiated alerting with a cost/benefit router: auto-apply low-risk/high-confidence, batch-and-rank ambiguous items, drop the rest; route **confidently-novel** items to review, not just low-confidence ones (Horvitz 1999; Alkhatib 2019). Surface capability + expected error rate + why on every output (Amershi).

**Why this is gated on measurement.** The router assumes PI review improves the result — the exact premise Jacobs 2021 puts in doubt (§0b.1). **So before building the router, instrument the calibration check: are PI-approved writes measurably more correct than raw engine writes?** If not, the fix is a different division of labor, not a better router. Build the measurement first.

### 3.6 Constrained decoding as the engine-layer contract — **Amend ADR-30, ADR-42, ADR-90, ADR-99** · status: measured ✓

**What.** Every ingest engine = decomposed, per-aspect, schema-constrained prompts + a tiny deterministic resolver; the **MASSW five-aspect schema** with mandatory "N/A" for absent aspects (Zhang 2024); temperature=0; closed label sets shown explicitly.

**Why + measured.** Constrain the output, not the model (Schick & Schütze 2021). **On-box: frozen qwen2.5:7b + Ollama `format=schema` is 6/6 clean on MASSW aspect extraction — the CrossTrace "~0% compliance" Refute does not reproduce on our task, and no QLoRA is budgeted.** Two standing caveats: constrained decoding forces *valid, not correct* (re-validate content, budget for backtracking — LMQL/Beurer-Kellner 2023); self-consistency is a closed-label router, not a faithfulness signal (§3.3). Faithfulness comes from deterministic grounding (§3.2), not agreement.

**Concrete.** One prompt per aspect; gate-existence-before-extraction to kill hallucinated claims; counterfactual perturbation to confirm the extractor tracks text. Re-test compliance on full-body / messy-OCR inputs (`probe-qwen-compliance.py --body`) before relying past abstracts.

---

## 4. New capabilities — mostly deferred past alpha.9

Adopt-grade in the literature, but not earned for this checkpoint (see §1 cut line). Listed for the roadmap.

- **4.1 Retriever/scout** (New / extend ADR-37, 65, 92) — instruction-tuned dense encoder over the **contextual round** (atom as index key, not stored unit — §0b.2), BM25 fallback, reasoning-trace query expansion, small-k LLM-judge reranker, offline hypothetical-question enrichment. Cap aggregated evidence at ~3 docs for qwen-class (Neekhra 2026). *Defer: retrieval quality matters most but the overhaul is post-alpha.9.*
- **4.2 Cheap non-LLM methods ahead of every model pass** (ADR-93, 94, 33) — MinHash-LSH dedup, PMI/class-TF-IDF keyphrases + cluster labels, per-aspect coding-then-clustering, random-walk-with-restart with path explanations. *Pull forward the dedup/keyphrase pieces if cheap.*
- **4.3 Two-stage normalize/dedup** (ADR-94) — embedding shortlist → small-LLM pick, keyed on canonical IDs (LLMs mint near-duplicate entities).
- **4.4 Typed-relation vocabularies + constructive-necessity test** **[paper-only]** (ADR-98, 52, 79) — citation-intent + functional-role taxonomies; record explicit NONE rather than forcing a citation (which also surfaces a gap). Schema as deliberate lossy KR (Davis).
- **4.5 Editable exemplar store — no training** (ADR-35, 23) — PI-confirmed exemplars in FAISS so a gate correction shifts future extractions; reject weight-internalized preferences (NanoResearch). *This is also the §0c "one-action-many-signals" lever.*
- **4.6 Negative-results / seen-dismissed store** (ADR-100, 61/95) — never re-surface rejected directions.

---

## 5. Evaluation & instrumentation — **Amend ADR-62, ADR-104/105/106, ADR-29, ADR-80**

The **first build here is the Jacobs calibration check** (§3.5 / §0b.1) — everything else is standard hygiene:

- **State-based evaluation + pass^k consistency** — judge resulting vault state vs expected; certify all-k succeed, not best-of-k (tau-bench 2024).
- **Groundedness as a gate metric** — NLI-entailment citation recall/precision over decomposed atomic sub-claims (ALCE/Gao 2023); the §3.2 lexical span-overlap is the cheap deterministic substitute.
- **Validate LLM-judges against the PI's own approve/reject labels** before trusting them; treat the score as triage, not certification.
- **Reward abstention** as a correct output (DOCBENCH, BBQ, TEMPO).
- **Trivial-control baselines** (majority-class, always-accept-venue) so triage gains aren't distributional shortcuts.
- **Bootstrap fixtures** by model-writing + PI-validating a sample (Perez 2022) and controlled mutation (negation/generalize) — but every threshold tuned on PI notes is **spent supervision** (§0c); freeze, version-pin, never report quality on the tuning set. Surface metrics (BLEU/ROUGE) track human judgment weakly — use process/abstention scoring.

---

## 6. Surfaces — projection, inspector, dashboards — **Amend ADR-102/103, ADR-84, ADR-87, ADR-71, ADR-101**

- **Render over native inspectable artifacts** (markdown / JSON Canvas / static HTML); diff-re-project by stable key (citekey/claim-id) so layout survives (D³/Bostock 2011).
- **Encode the single highest-priority signal preattentively** (contradiction / uncertainty / supersession); precompute conjunctions as their own mark; cap categorical color (Healey & Enns 2012).
- **Show evidence weight + dissent + a no-suggestion baseline, never a single persuasive rationale** — confident wrong outputs and tidy explanations actively harm an expert (Jacobs 2021, Govers 2026). The contradictions dashboard shows support/contradict **counts with provenance**, not "X% agree."
- **Expose what was down-ranked / suppressed** — applies to the triage ranker *and* the §3.4 supersession filter, so minority/superseded claims aren't silently hidden.
- **Computational wear** (render the PI's read/edit history as salience), **token-tiered projection** (statements-only first, escalate on low confidence — Knows/Yu 2026), **faceted navigation** over typed metadata with live counts (Hearst 2009).

---

## 7. Refuted / dropped — what measurement or the refutation pass killed

Recording these so they are not silently re-proposed:

- **QLoRA fine-tuning budget** — dropped; frozen + constrained decoding measured sufficient on our tasks (§3.6).
- **Holistic LLM "same variable?" gate** — dropped; recall 1/6 (§3.1). Use the decomposed gate only.
- **"NLI cleanly replaces cosine"** — narrowed; NLI fabricates different-variable contradictions, needs the structured gate, and cosine stays as a control (§3.1).
- **Atomic claim as the *stored* unit** — narrowed to *index* over the contextual round (§0b.2, §4.1).
- **Typed graph as a primary surface "at scale"** — demoted to one optional projection that must beat a BM25+dense baseline (§0b.3).
- **"Self-consistency is a free confidence signal"** — false; it is the largest compute line and blind to stable fabrication; closed-label router only (§3.3/§3.6).
- **"Least-privilege is sufficient security"** — narrowed to *necessary, not sufficient*; the gate is named as the (imperfect, itself-injectable) integrity control (§0b.5).
- **Per-item human gate** — narrowed to a sparse, uncertainty-routed gate (§3.5).

---

## 8. Open questions & untested risks

1. **The Jacobs question (highest).** Do PI-approved writes actually beat raw engine writes? Untestable here — needs real approve/reject logs. Until answered, the gate's value is assumed, not known. **ADR-03/57/24.**
2. **Real-claim re-runs.** The §3.1/§3.2/§3.6 numbers are smoke tests on hand fixtures + abstracts. Re-run on real vault claims (`current-state-baseline.md`, `probe-qwen-compliance.py --body`) before any threshold is set.
3. **Relationship-extraction quality** (the new §3.1 bottleneck) — negation, argument-order, same-attribute/different-value. Is a better-prompted decomposed extractor enough, or does this need its own small model?
4. **Evidence-strength / source-type provenance** (§3.3) — Zotero item-type gives review-vs-primary cheaply; evidence-strength may need a classifier or PI tagging.
5. **Schema migration** (§3.3/§3.4) — backfill epistemic/temporal fields on existing claims: one-time pass with PI spot-check, or lazy-on-touch?
6. **The untested literature Refutes** (§0b.2–4) — atomic-as-unit, graph<BM25, proposer precision — all need labeled vault data.

---

## 9. ADR worklist (proposed)

| Disposition | ADRs | Item | Status |
|---|---|---|---|
| Amend | 30, 42, 90, 99 | §3.6 constrained decoding | measured ✓ ship |
| Amend | 03, 57, 79 | §3.2 warrant checker | measured ✓ ship |
| Amend | 56, 08, 50 | §3.3 epistemic status | ship (foundational) |
| Retire+Amend | 09, 10, 94, 38 | §3.1 NLI + decomposed gate | measured-partial |
| Amend | 70, 81, 41, 03 | §3.5 gate router + Jacobs check | **measure first** |
| Amend | 10, 09, 92, 65 | §3.4 supersession + temporal | |
| Validate (caveated) | 03, 57, 32, 46, 28, 27, 01, 22, 24 | §2 skeleton | strong form contested |
| New / extend | 37/65/92, 93/94/33, 98/52/79, 35/23, 100/61/95 | §4 (deferred past alpha.9) | |
| Amend | 62, 104/105/106, 29, 80 | §5 evaluation (Jacobs check first) | |
| Amend | 102/103, 84, 87, 71, 101 | §6 surfaces | |

---

## 10. Provenance

- **Corpus:** 401 papers, `_papers/` (Zotero export `_papers/Exported Items.bib`).
- **Pass 1 — review:** `_papers/REVIEW-SUMMARY.md` (executive summary, 9 themes, 11 category deep-dives).
- **Pass 2 — refutation:** `_papers/REVIEW-REFUTATIONS.md` (14 bets attacked, 0 survived intact).
- **Pass 3 — measurement:** `spike-nli-vs-cosine.py` (cosine/NLI/gate), `probe-qwen-compliance.py` (frozen-model aspect + warrant compliance), `current-state-baseline.md` (the PI-fills instrument).
- **Per-paper verdicts:** `_notes/paper-review-verdicts.json`.
- **Docs already wired to the review:** PR #784 (`intellectual-foundations.md`, `why-pattern-provenance.md`, `bibliography.md`).
