# Memoria design-update recommendations — alpha.9

_Working artifact for the 0.1.0-alpha.9 checkpoint; deleted before the release closes (AGENTS.md). Decisions land in ADRs — this doc proposes them._

_Built in four passes: a 401-paper literature review (`_papers/REVIEW-SUMMARY.md`), an adversarial refutation pass (`_papers/REVIEW-REFUTATIONS.md`), **on-box measurement** of the contested claims (`spike-nli-vs-cosine.py`, `probe-qwen-compliance.py`), and a **grounding pass** that re-pointed every recommendation at the components Memoria actually ships. This rewrite folds all four in; the earlier confirmation-first and greenfield framings are superseded._

## How to read this

Four passes, in increasing trust:

1. **Literature review** — confirmation-biased; claimed the corpus "re-derives" Memoria's design. Treat with suspicion.
2. **Refutation** — attacked 14 load-bearing bets; **none survived intact**. The corpus endorses the skeleton and refutes most strong claims layered on top.
3. **On-box measurement** — the contested, testable claims, run on the real box. Measurement beats both the literature and the refutation.
4. **Grounding** — the recommendations were written *without* reference to the running system, so they recommended building things that already exist. Every item is now anchored to a deployed component or marked as shaping an unbuilt proposal.

**Trust order: measured > refuted > literature-pull.** Disposition tags: **Validate / Amend / Retire / Tension / New**. Read every "Amend" through the built-vs-proposed map in §0c — amending a *built* component is a change to deployed behaviour; against a *proposed* ADR it only shapes the unbuilt thing.

---

## 0. The state of play — read before §1

### 0a. What we measured on-box (highest confidence)

Run on the RTX 4060 Ti with `qwen2.5:7b` — the local **test** model. The live engines call an **LLM API** (§0c), so these are **pessimistic floors**: a more-capable API does at least as well.

| Contested claim | Measured (test-model floor) | Verdict |
|---|---|---|
| Cosine arbitrates same/contradicts | 0/8 on word-overlap/opposite-meaning pairs (all rated "same", 0.78–1.00) | **Blind spot confirmed** — retire cosine as the *arbiter* |
| NLI fixes it | 8/8 on the same trap; direction-stable; **<0.6 GB VRAM** | NLI clears the *easy* trap; predicted HANS failure didn't appear |
| NLI is clean | On same-topic / **different-variable** pairs it **confidently fabricates contradictions at 0.94–1.00** | NLI alone is a false-contradiction generator; a confidence threshold can't filter it |
| Variable-match gate fixes that | Holistic LLM "same variable?" → **recall 1/6**; decomposed (entity+attribute+direction) → **recall 4/6, FP dropped 6/7** | **Necessary, not sufficient**; bottleneck moves to direction/relationship extraction |
| Frozen small local model ≈ 0% schema compliance (CrossTrace) | MASSW aspect **6/6 clean** (`format=schema`); verbatim warrant quotes **90% (18/20)** | **Refuted** — even the test floor clears it; §3.6 confirmed, **QLoRA dropped** |

Caveat for all of the above: hand fixtures (~20–30 pairs) + abstract/intro text — **go/no-go smoke tests, not benchmarks**. Re-run on real vault claims (`current-state-baseline.md`) before any threshold is trusted.

### 0b. What the literature refutes but we couldn't test here (warnings, ranked by blast radius)

1. **Human + machine ≯ machine — the gate's premise may be false.** Jacobs 2021 (N=220): clinician+ML ≈ clinician-alone, both far below ML-alone; a *wrong* output dragged the human *below* baseline. If this holds, "PI approves" doesn't improve correctness and the gate is theater. The **existential risk** — and now cheaply testable (§1, §5), because the gate plugin and telemetry are already built. **ADR-03/57/24.**
2. **Atomic-as-stored-unit hurts QA** — the contextual round is the retrieval unit, the atom an index over it (LongMemEval, Hu 2026).
3. **Durable graph memory underperforms BM25** (MemoryAgentBench) — and BM25 is *already* half of `qmd`, so the real test is **graph vs. `qmd`** on the vault.
4. **Automatic contradiction/supersession is the least-reliable memory capability** (~28% wrong flips, Mitchell 2022). The §3.1 gate test already shows the proposer is lossy.
5. **Least-privilege ≠ security against poisoned papers** — the dominant threat is untrusted *data*, not code (Greshake, Debenedetti). Architectural, not benchmarkable.

### 0c. Binding constraints + the deployed components (apply to everything below)

- **Engines call an LLM API, not a local model.** `qwen2.5:7b` (local, Ollama) is the **test fixture**; the live extraction/judging engines call an **LLM API**. Consequences: (a) on-box qwen numbers are **floors**; (b) ingest cost is **API spend per document**, so self-consistency (5–10× per aspect) is a real money line — not free GPU time; (c) vault/claim text **leaves the machine** on every call, so "keep the bits local" doesn't describe the live system (part of the §0b.5 data-attack-surface). The NLI comparator, embeddings, and dedup can still be local.
- **Retrieval is `qmd` (deployed).** A shared **local hybrid index — BM25 + vector + cross-encoder rerank** — read-only MCP+CLI behind Co-PI/Librarian/Writer/Peer-reviewer and the pre-file gate (ADR-38; `docs/reference/search.md`). No network leaves the machine. §3.1/§4.1/§4.3 are **deltas to qmd**; the baseline-to-beat **is qmd**. The cosine §3.1 retires-as-arbiter is qmd's vector half; the reranker §1 tests is qmd's existing cross-encoder.
- **Built vs proposed (the grounding map).** *Built (accepted ADR + code):* `qmd` (38), **`cluster_mcp`** (33: NetworkX communities + JSON-Canvas + **BERTopic/UMAP+HDBSCAN**), the **`memoria-policy-gate`** plugin (28/03/57), **contradictions dashboard** (09) + **supersession** (10), deterministic ingest (30), telemetry (104/105/106), spaces (101). *Proposed / not built (shaping, not amending):* LTR-triage (89), claim-sentence-classification (90), discovery-scoring (92), keyphrase (93), record-linkage dedup (94), relation-vocab (98), MASSW-aspects (99), projection-engine (102/103).
- **Content scope.** Papers (Zotero, ADR-05/06/99) *plus* the PI's own notes. **[paper-only]** items (§3.3 primary-vs-review weighting, §4.4 citation-intent) need a DOI + citation graph and don't apply to non-paper notes.
- **Single PI-supervision budget.** One human, no co-PI. NLI calibration, POTENTIAL review, novelty escalation, judge validation, exemplar corrections, schema spot-checks all draw on the *same* attention. Set one annual label ceiling; design for **one PI action emitting many signals**; model gate throughput, not just label count.
- **Need-push, not literature-pull.** §1's order is research-derived, not yet validated against observed alpha.9 pain. Fill `current-state-baseline.md` and re-rank before committing.
- **Benchmarks are external.** Point estimates are one paper's setup; the *direction* survives, the *digits* must be re-measured in-domain.

### 0d. The open architecture question the grounding surfaced

Two grounded facts collide: API ingest carries **cost + data-egress** on the highest-volume path, *and* the local test model already does structured extraction competently (6/6 aspects, 90% warrants). Together they reframe the qwen results as evidence that **local extraction is viable** — which matters precisely because API-on-every-ingest is expensive and sends vault text off-machine. This raises (does **not** decide): *should high-volume ingest extraction run on a local model, with the API reserved for low-volume hard judging?* Flagged as §8.1; not assumed here.

---

## 1. What to do for alpha.9 — re-pointed at deployed components

Re-ordered after grounding. The first two are **cheap tests against already-built components** that can change everything downstream; ship the measured-green items alongside; defer the unbuilt.

**Near-term tests (cheap, deployed component, high information value):**
1. **Evaluate `qmd`'s existing reranker.** qmd already cross-encoder-reranks, and off-the-shelf cross-encoders *hurt* on reasoning-relevance (Wei 2026) — the exact cross-paper queries Memoria depends on. Test qmd-rerank-on vs -off over ~20 real reasoning queries. Possible **quick win** (disable a hurting stage) or a real gap. (§4.1)
2. **Instrument the Jacobs check on the built gate.** "Do PI-approved writes actually beat raw engine writes?" The gate plugin + telemetry planes already exist (ADR-28/104/105/106), so this is **wiring, not building** — and it's the existential question (§0b.1). (§3.5, §5)

**Ship (measured-green, cheap because they amend built components):**
3. **Constrained-decoding engine contract** (§3.6) — *measured 6/6*; amends built ingest (ADR-30).
4. **Model-free warrant checker** (§3.2) — *measured 90% verbatim*; a new check in the built gate plugin.
5. **Epistemic-status claim fields** (§3.3) — extends the built uncertainty-flag (ADR-56); precondition for §3.1's gate.

**Build with care (measured-partial):**
6. **NLI relationship verdict + decomposed variable-match gate** on top of qmd (§3.1) — precision win, measured recall cost; propose-only.

**Defer past alpha.9** (proposed/unbuilt, or earned only after the tests): qmd tuning beyond the reranker test (§4.1), the typed graph (must beat qmd — §0b.3), dedup/keyphrase/LTR (§4.2/§4.3, all proposed), the exemplar store (§4.5).

**Explicitly NOT doing:** QLoRA (refuted); ripping out cosine wholesale (it's qmd's vector half — keep it as the retriever, retire only its *arbiter* role); auto-applied contradiction/supersession links (propose-only); **blanket self-consistency** (§3.6 — an API bill now, and the API is reliable enough at structure to skip it there).

---

## 2. Validated skeleton — backing holds; strong form of four rows contested (§0)

| Design bet | Status | ADRs |
|---|---|---|
| Engines write, agents judge, PI approves | ⚠ strong form **untested & at risk** (Jacobs, §0b.1) — now cheaply testable | 03, 57, 14, 21, 41, 82 |
| MCP-only sandbox (no file/terminal/code-exec) | ⚠ necessary, **not sufficient** (data > code, §0b.5) | 32, 46, 28, 27 |
| Vault-as-memory / durable artifacts | ✓ validated | 01, 46, 23 |
| Atomic claims store | ⚠ as *index*, not *stored unit* (§0b.2) | 90, 56, 99 |
| Deterministic ingest (LLM via API; qwen for tests) | ✓ deterministic-ingest measured-confirmed on the floor (§0a); "local model" was the test split, not the live engine (§0c) | 30, 108 |
| Faithfulness over flash | ✓ validated | 22, 24 |

---

## 3. Sharpenings — amend the built components

### 3.1 Contradiction / dedup / supersession: NLI on top of `qmd`, gated by structured variable-match — **Retire (cosine-as-arbiter) + Amend ADR-09, ADR-10, ADR-38 (built); shape ADR-94** · status: measured-partial

**What.** This sits **on top of `qmd`, not instead of it**: qmd retrieves candidate pairs; a **local NLI comparator** (FEVER tri-class SUPPORTED/REFUTED/NOTENOUGHINFO, carrying its evidence sentence) gives the **relationship verdict** over those candidates; the verdict feeds the **built contradictions dashboard** (ADR-09) and **supersession** (ADR-10). A contradiction/dedup edge additionally requires a **decomposed variable-match** — `(entity, attribute, direction)` as *separate* fields (§3.3), entity+attribute match with direction-conflict — **never a holistic LLM "same variable?" call**. What's retired is qmd's **vector similarity as the contradiction *arbiter*** (the pre-file gate, ADR-38), not qmd as the retriever. Edges **proposed, never auto-applied**.

**Why + measured.** Cosine is negation-blind (0/8, §0a). NLI clears that trap (8/8) but **confidently mints false contradictions on different-variable pairs** (0.94–1.00) — a confidence threshold can't filter it, so the variable-match gate is a **precondition**. The gate measured: holistic recall 1/6 → decomposed 4/6, FP dropped 6/7; the residual losses (negation, argument-swap, same-attribute/different-value) are **relationship-extraction failures**, now the hard part. Prefer `MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli`; read `id2label` (never hardcode).

**Concrete.** Local ANLI/FEVER NLI under MCP (<0.6 GB) over qmd candidates; verdict gated by decomposed variable-match; MaxSAT consistency only over *gated* edges (ConCoRD/Mitchell 2022); track **proposer precision** before any promotion (least-reliable capability); keep the HANS/trap + different-variable NEUTRAL fixtures as regression tests.

### 3.2 Model-free warrant checker in the gate plugin — **Amend ADR-03, ADR-57, ADR-79 (built `memoria-policy-gate`)** · status: measured ✓

**What.** A **deterministic, no-LLM** check added to the built gate plugin: substring grounding of the verbatim warrant quote, entity-type compatibility, year-ordering, opposite-direction-edge check, citekey resolves. Structural validity machine-checked; semantic correctness deferred to agent/PI.

**Why + measured.** Bare LLM judges err 16–46% and post-rationalize citations; an injection fools the judge too (CiteGuard, Wallat 2024, AgentDojo). **On-box: 90% of warrant quotes are exact substrings — the checker passes those, rejects the 10%.** Field separation (resolved): the **warrant is the verbatim span** (checkable); the **claim text is normalized** (never substring-matched against source).

**Concrete.** Fail-fast lint stage in the plugin; reject any edge lacking a correct warrant. Offline causal-faithfulness counterfactual (decoy-source re-citation → low-confidence — Wallat 2024).

### 3.3 Epistemic status as first-class claim data — **Amend ADR-56 (built uncertainty-flag); shape ADR-90, ADR-52, ADR-50**

**What.** Every claim/relation carries: uncertainty flag, source-span provenance grade (complete/partial/broken), two-axis confidence, source-document-type **[paper-only]** (review/primary/preprint) + evidence-strength, a `source_anchor`. Contradiction/supersession privilege primary evidence over echoed consensus.

**Why.** LM fluency is not knowledge (Bender 2021). The `(context, variables, relationship)` decomposition is what §3.1's gate consumes — build it once. **Version-pin epistemic metadata** to model + prompt — *more* important with an API the provider silently updates. Self-consistency can feed uncertainty, but **only on closed-label steps** and at API cost (§3.6).

**Concrete.** Extend the built claim/source-note frontmatter; backfill is open (§8).

### 3.4 Supersession as a deterministic retrieval filter; time as a first-class field — **Amend ADR-10, ADR-09 (built); shape ADR-92**

**What.** A deterministic filter over an **append-only** `replaces` chain (`record_status: superseded`, `stale_after`), with **ISO temporal scope + tense + confidence** on every claim and **Temporal Coverage@k** on the scout; abstain when evidence is time-mismatched.

**Why + caution.** Forgetting, not recall, is the universal memory failure; temporally-incomplete retrieval actively harms output (TEMPO/Abdallah 2026). **But the filter can silently suppress correct claims** — keep superseded claims **retrievable** (tagged), penalize *stale-as-current reuse* rather than hard-excluding, and **expose what the filter dropped** (§6). Cross-period queries need both baseline and current claim.

**Concrete.** Append-then-compete (successor re-passes the gate); meaning-changed-vs-cosmetic classifier on re-ingest (Du 2022); forgetting-aware metric.

### 3.5 Gate router — but instrument the Jacobs question first — **Amend ADR-70, ADR-81, ADR-41, ADR-03 (built gate + dashboards)**

**What.** Replace undifferentiated alerting in the built gate with a cost/benefit router: auto-apply low-risk/high-confidence, batch-and-rank ambiguous, drop the rest; route **confidently-novel** items to review, not just low-confidence (Horvitz 1999; Alkhatib 2019).

**Why this is gated on measurement.** The router assumes PI review improves the result — the premise Jacobs 2021 doubts (§0b.1). **Because the gate plugin and telemetry already exist, instrument the calibration check first** (do PI-approved writes beat raw engine writes?) — it's wiring, not building. If the answer is no, the fix is a different division of labor, not a better router.

### 3.6 Constrained decoding as the engine-layer contract — **Amend ADR-30 (built ingest); shape ADR-42→48, ADR-90, ADR-99** · status: measured ✓

**What.** Decomposed, per-aspect, schema-constrained prompts + a tiny resolver; the **MASSW five-aspect schema** with mandatory "N/A" (Zhang 2024); temperature=0; closed label sets shown explicitly.

**Why + measured.** Constrain the output, not the model. **On-box (test floor): qwen + `format=schema` is 6/6 clean** — CrossTrace's Refute doesn't reproduce, no QLoRA. **Self-consistency, re-scoped by the API fact:** on a local model it was free; on the API it's a per-token bill on the hot path, *and* the API is more reliable at structure than the qwen floor — so **don't sample 5–10× for structure** (take the API's valid JSON directly); reserve self-consistency, if at all, for genuine *uncertainty* on closed-label steps. Constrained decoding still forces *valid, not correct* — re-validate content (LMQL/Beurer-Kellner 2023). Faithfulness comes from deterministic grounding (§3.2), not agreement.

**Concrete.** One prompt per aspect; gate-existence-before-extraction; re-test compliance on full-body / messy-OCR (`probe-qwen-compliance.py --body`) before relying past abstracts.

---

## 4. New capabilities — proposed/unbuilt, deferred past alpha.9 (except 4.1's reranker test)

- **4.1 Retriever/scout — extend `qmd`, don't rebuild** (shape ADR-48, 92, 98/99/100) — qmd is *already* hybrid BM25+vector+rerank. Deltas: index the **contextual round** (not whole notes); reasoning-trace query expansion; **evaluate qmd's existing reranker** (the §1 near-term test — Wei 2026 says cross-encoders hurt on reasoning-relevance); offline hypothetical-question enrichment. Cap aggregated evidence ~3 docs (Neekhra 2026).
- **4.2 Cheap non-LLM methods** (proposed ADR-93, 94; clustering = delta to built ADR-33 `cluster_mcp`) — MinHash dedup + PMI/class-TF-IDF keyphrases are proposed/new. **Clustering already exists**: `cluster_mcp` runs NetworkX communities + BERTopic (UMAP+HDBSCAN). So per-aspect coding-then-clustering is a **delta to `cluster_model_topics`**, and RWR-with-path-explanations is an **added traversal on `cluster_build_graph`** — not a new stack.
- **4.3 Two-stage normalize/dedup** (proposed ADR-94) — **qmd's vector search** proposes the shortlist → small-LLM pick, keyed on canonical IDs.
- **4.4 Typed-relation vocabularies + constructive-necessity test** **[paper-only]** (shape ADR-98, 52, 79) — citation-intent + functional-role taxonomies; record explicit NONE (surfaces a gap). Schema as deliberate lossy KR (Davis).
- **4.5 Editable exemplar store — no training** (shape ADR-35, 23) — PI-confirmed exemplars so a gate correction shifts future extractions; reject weight-internalized preferences (NanoResearch). The §0c "one-action-many-signals" lever.
- **4.6 Negative-results / seen-dismissed store** (shape ADR-100, 61/95).

---

## 5. Evaluation & instrumentation — **Amend ADR-62, ADR-104/105/106 (built telemetry), ADR-29, ADR-80**

**First build: the Jacobs calibration check (§3.5, §0b.1)** — wired into the existing telemetry planes, not new infra. Then standard hygiene:

- **State-based evaluation + pass^k consistency** (tau-bench 2024).
- **Groundedness as a gate metric** — NLI-entailment citation recall/precision over decomposed sub-claims (ALCE/Gao 2023); §3.2's span-overlap is the cheap deterministic substitute.
- **Validate LLM-judges against the PI's own approve/reject labels**; triage signal, not certification.
- **Reward abstention** (DOCBENCH, BBQ, TEMPO); **trivial-control baselines** (majority-class, always-accept-venue).
- **Bootstrap fixtures** by model-writing + PI-validating a sample (Perez 2022) — every threshold tuned on PI notes is **spent supervision**; freeze, version-pin. Surface metrics (BLEU/ROUGE) track human judgment weakly — use process/abstention scoring.

---

## 6. Surfaces — projection, inspector, dashboards — **Amend ADR-101 (built spaces); shape ADR-102/103 (projection-engine, proposed)**

- **Render over native inspectable artifacts** (markdown / JSON Canvas — the `cluster_emit_canvas` output / static HTML); diff-re-project by stable key (D³/Bostock 2011).
- **Encode the single highest-priority signal preattentively** (contradiction / uncertainty / supersession); precompute conjunctions; cap categorical color (Healey & Enns 2012).
- **Show evidence weight + dissent + a no-suggestion baseline, never a single persuasive rationale** — confident wrong outputs and tidy explanations actively harm an expert (Jacobs 2021, Govers 2026). The contradictions dashboard shows support/contradict **counts with provenance**, not "X% agree."
- **Expose what was down-ranked / suppressed** — the triage ranker *and* the §3.4 supersession filter.
- **Computational wear** (PI's read/edit history as salience), **token-tiered projection** (statements-only first — Knows/Yu 2026), **faceted navigation** over typed metadata with live counts (Hearst 2009).

---

## 7. Refuted / dropped — so they aren't re-proposed

- **QLoRA fine-tuning** — the live engine is an API (not fine-tuneable), and the test floor already clears the task (§3.6).
- **Holistic LLM "same variable?" gate** — recall 1/6 (§3.1). Decomposed only.
- **"NLI cleanly replaces cosine"** — narrowed; NLI fabricates different-variable contradictions, needs the structured gate; cosine stays as qmd's retriever.
- **Greenfield retriever / clustering stack** — `qmd` and `cluster_mcp` already exist; these are deltas, not builds (§4.1/§4.2).
- **Blanket self-consistency** — an API bill now, and the API is reliable enough at structure to skip it there (§3.6).
- **Atomic-as-stored-unit** — narrowed to *index* (§0b.2). **Typed graph "at scale"** — must beat qmd (§0b.3).
- **"Self-consistency is a free confidence signal"** / **"Least-privilege is sufficient security"** / **per-item gate** — all narrowed (§0).

---

## 8. Open questions & untested risks

1. **Local-vs-API ingest (new, §0d).** Given API cost + data-egress on the hot path and the local model's measured extraction competence — should high-volume ingest run locally, API reserved for low-volume judging?
2. **The Jacobs question (highest).** Do PI-approved writes beat raw engine writes? Now wireable into existing telemetry — do it first.
3. **Does qmd's reranker help or hurt** on reasoning-relevance? The §1 near-term test.
4. **Real-claim re-runs.** The §3.1/§3.2/§3.6 numbers are smoke tests; re-run on real vault claims before any threshold.
5. **Relationship-extraction quality** (the §3.1 bottleneck) — negation, argument-order, value-conflict. Better prompt, or its own model?
6. **Schema migration** (§3.3/§3.4) — backfill epistemic/temporal fields: one-time pass or lazy-on-touch?

---

## 9. ADR worklist (proposed)

| Disposition | ADRs | Item | Status |
|---|---|---|---|
| **Test first** | 38 (qmd), 104/105/106 (telemetry) | §1 qmd-reranker eval + Jacobs check | cheap, deployed |
| Amend (built) | 30 | §3.6 constrained decoding | measured ✓ ship |
| Amend (built) | 03, 57, 79 | §3.2 warrant checker | measured ✓ ship |
| Amend (built) + shape | 56; 90, 52, 50 | §3.3 epistemic status | ship |
| Retire+Amend (built) | 09, 10, 38; shape 94 | §3.1 NLI on qmd + decomposed gate | measured-partial |
| Amend (built) | 70, 81, 41, 03 | §3.5 gate router | **measure first** |
| Amend (built) | 10, 09; shape 92 | §3.4 supersession + temporal | |
| Validate (caveated) | 03, 57, 32, 46, 28, 27, 01, 22, 24 | §2 skeleton | strong form contested |
| Shape (proposed) / delta | 48/92/98/99/100, 93/94, 33-delta, 98/52/79, 35/23, 100/61/95 | §4 (deferred) | |
| Amend (built) | 62, 104/105/106, 29, 80 | §5 evaluation (Jacobs first) | |
| Amend/shape | 101; 102/103 | §6 surfaces | |

---

## 10. Provenance

- **Corpus:** 401 papers, `_papers/` (Zotero export `_papers/Exported Items.bib`).
- **Pass 1 — review:** `_papers/REVIEW-SUMMARY.md`. **Pass 2 — refutation:** `_papers/REVIEW-REFUTATIONS.md` (0/14 bets survived intact).
- **Pass 3 — measurement:** `spike-nli-vs-cosine.py` (cosine/NLI/gate), `probe-qwen-compliance.py` (extraction/warrant on the qwen test floor), `current-state-baseline.md` (PI-fills instrument).
- **Pass 4 — grounding:** anchored to `qmd` (search), `cluster_mcp` (clustering, ADR-33), `memoria-policy-gate` (write gate, ADR-28), the contradictions dashboard (ADR-09), and the built-vs-proposed ADR statuses.
- **Per-paper verdicts:** `_notes/paper-review-verdicts.json`. **Docs wired to the review:** PR #784.
