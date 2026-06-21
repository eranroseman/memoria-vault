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

### 0a. KNOWN — measured on-box, in-domain (the only rows we actually know)

_These ~6 rows are the document's only unbiased instrument. Everything outside them (§0b, §3–§6 rationale) is a **warning or a prior**, not knowledge. By volume the doc is mostly literature/refutation; by knowledge it is this table. Both the confirmation pass (built to confirm → confirmed) and the refutation pass (built to refute → refuted) are method artifacts; only measurement escapes that._

Run on the RTX 4060 Ti with `qwen2.5:7b` — the local **test** model. The live engines call an **LLM API** (§0c), so these are **pessimistic floors**: a more-capable API does at least as well.

| Contested claim | Measured (test-model floor) | Verdict |
|---|---|---|
| Cosine arbitrates same/contradicts | 0/8 on word-overlap/opposite-meaning pairs (all rated "same", 0.78–1.00) | **Blind spot confirmed** — retire cosine as the *arbiter* |
| NLI fixes it | 8/8 on the same trap; direction-stable; **<0.6 GB VRAM** | NLI clears the *easy* trap; predicted HANS failure didn't appear |
| NLI is clean | On same-topic / **different-variable** pairs it **confidently fabricates contradictions at 0.94–1.00** | NLI alone is a false-contradiction generator; a confidence threshold can't filter it |
| Variable-match gate fixes that | Holistic LLM "same variable?" → **recall 1/6**; decomposed (entity+attribute+direction) → **recall 4/6, FP dropped 6/7** | **Necessary, not sufficient**; bottleneck moves to direction/relationship extraction |
| Frozen small local model ≈ 0% schema compliance (CrossTrace) | MASSW aspect **6/6 clean** (`format=schema`); verbatim warrant quotes **90% (18/20)** | **Refuted** — even the test floor clears it; §3.6 confirmed, **QLoRA dropped** |

Caveat for all of the above: hand fixtures (~20–30 pairs) + abstract/intro text — **go/no-go smoke tests, not benchmarks**. Re-run on real vault claims (`current-state-baseline.md`) before any threshold is trusted.

### 0b. WARNINGS — others' measurements, not ours (not in-domain knowledge, ranked by blast radius)

_These are real findings from other people's studies, in other domains — credible enough to watch, not validated for Memoria. Each one's remedy is to **convert it into an §0a row** by measuring in-domain (gate logs, vault corpus), not to read more papers. Until then they are warnings, not facts._

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
- **Single PI-supervision budget — do the arithmetic, because it breaks the program.** One human, no co-PI. ~9 sinks draw the *same* attention: Jacobs ground-truth re-checks, NLI threshold calibration, judge-vs-PI validation, the POTENTIAL middle, novelty escalation, exemplar corrections, relationship-extraction fixtures, evidence-strength tagging, schema spot-checks. Two hard consequences the rest of this doc must respect: **(1) Jacobs-grade rigor is unreachable.** Jacobs was N=220; a single PI realistically labels dozens, not hundreds — so every in-domain measurement here is **low-power, directional-only**, and a clean "the gate helps / doesn't" verdict is *not* on offer. Design the measurements to ride on normal use (one approve/reject → many signals), never as standalone studies. **(2) The proposal queue is a budget line, and at low precision it dominates.** A propose-only feature at Mitchell's ~28% precision yields ~2–3 bad proposals per good one; a 50-flag/week queue ≈ 35 wasted reviews/week ≈ the whole budget. So **no propose-only capability ships without a measured precision floor _and_ a volume cap**; "propose-only" is not free — it is the most expensive default (see §3.1's re-tier).
- **Need-push, not literature-pull.** §1's order is research-derived, not yet validated against observed alpha.9 pain. Fill `current-state-baseline.md` and re-rank before committing.
- **Benchmarks are external.** Point estimates are one paper's setup; the *direction* survives, the *digits* must be re-measured in-domain.

### 0d. The open architecture question the grounding surfaced

Two grounded facts collide: API ingest carries **cost + data-egress** on the highest-volume path, *and* the local test model already does structured extraction competently (6/6 aspects, 90% warrants). Together they reframe the qwen results as evidence that **local extraction is viable** — which matters precisely because API-on-every-ingest is expensive and sends vault text off-machine. This raises (does **not** decide): *should high-volume ingest extraction run on a local model, with the API reserved for low-volume hard judging?* Flagged as §8.1; not assumed here.

### 0e. Error-cost model (N=1) — and the re-tier it forces

This is **one researcher's** vault, and error costs are **not flat** — so engineering every capability to the same precision is over-building. The tiers:

| Error class | Cost for an N=1 PI | Bar |
|---|---|---|
| **Faithfulness / provenance** — a claim cites a source that doesn't support it | **High — trust-destroying.** If the vault can't be trusted, it is worthless; the harm compounds silently. | **Keep rigorous** (§3.2). |
| **Fabricated auto-applied edit/merge** — corrupts canonical state | **High — but already neutralized** by propose-only + the gate. | Structural, not precision. |
| **Missed contradiction / stale claim resurfaces** | **Low — self-correcting.** The PI reads it, notices, moves on; nothing compounds. | **Soft-flag, not high precision.** |
| **Over-linking / false contradiction flag** | **Low-to-moderate — but bills the scarce budget** (§0c proposal queue). | Cap volume; precision floor. |

**The re-tier this forces:** the **faithfulness half** of §3 (the §3.2 warrant checker, citekey resolution, abstain-when-ungrounded) stays high-bar — it guards the high-cost error. The **contradiction-completeness half** (the §3.1 NLI + decomposed variable-match gate + MaxSAT apparatus) is **over-built for an error that's cheap to make and self-correcting**, and it bills the scarcest resource at low precision. So for alpha.9 it **collapses to a soft-flag** (§3.1); the precision apparatus is deferred until in-domain data shows the miss actually costs something. This deletes the most-engineered half of the agenda by design, not by caveat.

---

## 1. What to do for alpha.9 — re-pointed at deployed components

Re-ordered after the critiques. **#0 is the long pole — start it today**, because its data accrues over weeks and gates everything below it. Then the cheap deterministic ship-items and one cheap test. The big precision builds are **deferred by the §0e error-cost model**, not sequenced.

**0. START OBSERVING REAL USAGE TODAY (the actual #1).** Switch on **gate approve/reject logging + a periodic ground-truth re-check** (wiring the built gate plugin + telemetry, ADR-28/104/105/106), and **begin filling `current-state-baseline.md`** from real runs. This is the long pole: it's the only source of the in-domain data that (a) answers the existential Jacobs question (§0b.1) and (b) *re-ranks everything below* — until it returns, this §1 ordering is the literature-pull the doc tells you not to trust (§0c need-push). Everything else proceeds in parallel; this is the clock that must start now.

**Ship (cheap, deterministic, measured-green — amend built components):**
1. **Constrained-decoding engine contract** (§3.6) — *measured 6/6*; amends built ingest (ADR-30).
2. **Model-free warrant checker** (§3.2) — *measured 90% verbatim*; guards the **high-cost faithfulness error** (§0e); a new check in the built gate plugin.
3. **Epistemic-status claim fields** (§3.3) — extends the built uncertainty-flag (ADR-56).
4. **Contradiction soft-flag** (§3.1, re-tiered) — surface qmd's high-similarity pairs in the built dashboard as "possible conflict — check?"; **no NLI, no MaxSAT** for alpha.9 (§0e: the miss is low-cost).

**One cheap test (instant, may be a quick win):**
5. **Evaluate `qmd`'s existing reranker** — qmd already cross-encoder-reranks, and cross-encoders *hurt* on reasoning-relevance (Wei 2026); test rerank-on vs -off over ~20 real queries. Disable-a-hurting-stage win or a real gap. (§4.1)

**Deferred by §0e / §0c, not sequenced** (build only if in-domain data shows the cost): the full **NLI + decomposed-gate + MaxSAT** contradiction engine (§3.1 — gated on measured proposer precision *and* a measured cost-to-missing); the gate **router** (§3.5 — only after the Jacobs check returns); qmd tuning beyond the reranker test; the typed graph (must beat qmd, §0b.3); dedup/keyphrase/LTR (§4.2/§4.3, all proposed); the exemplar store (§4.5).

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

### 3.1 Contradictions — a cheap soft-flag for alpha.9; the NLI/gate apparatus deferred — **Amend ADR-09, ADR-10 (built); the NLI build shapes ADR-94, deferred** · status: re-tiered by §0e

**What (alpha.9).** A **soft-flag only.** `qmd` already surfaces high-similarity claim pairs; surface those to the **built contradictions dashboard** (ADR-09) as a low-confidence "**possible conflict — check?**" marker, with the pair and their source spans. No NLI model, no decomposed gate, no MaxSAT for alpha.9. Nothing auto-applies; the PI skims and dismisses cheaply. This is what the §0e error-cost model buys: a missed/late contradiction is **self-correcting and low-cost**, so it does not justify a precision engine.

**Why this is re-tiered down, not up.** The measurement (§0a) is real — cosine is negation-blind (0/8) and NLI on its own **confidently mints false contradictions** (0.94–1.00 on different-variable pairs), recoverable only by a decomposed variable-match gate that itself measured 4/6 recall and still leaks (negation, argument-swap). So the *full* fix is an NLI comparator + `(entity, attribute, direction)` extraction + MaxSAT — a large build whose residual is **relationship-extraction quality** (§8.5). Under §0e that build is **over-engineered for a low-cost error**, and under §0c its propose-only queue (~28% precision, Mitchell) would dominate the supervision budget. So it is **deferred**, not shipped — gated on in-domain data (proposer precision on real flags, §1) showing the miss actually costs something.

**Deferred build (only if the data justifies it).** Local ANLI/FEVER NLI (`MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli`, read `id2label`) over qmd candidates → decomposed variable-match gate → MaxSAT over gated edges only (ConCoRD/Mitchell 2022); keep the HANS/trap + NEUTRAL fixtures as its regression set. Trigger: measured proposer precision high enough **and** a measured cost to missing contradictions. Cosine stays qmd's retriever throughout; only its *arbiter* role is retired (a soft-flag is not an arbiter).

### 3.2 Model-free warrant checker in the gate plugin — **Amend ADR-03, ADR-57, ADR-79 (built `memoria-policy-gate`)** · status: measured ✓

**What.** A **deterministic, no-LLM** check added to the built gate plugin: substring grounding of the verbatim warrant quote, entity-type compatibility, year-ordering, opposite-direction-edge check, citekey resolves. Structural validity machine-checked; semantic correctness deferred to agent/PI.

**Why + measured.** Bare LLM judges err 16–46% and post-rationalize citations; an injection fools the judge too (CiteGuard, Wallat 2024, AgentDojo). **On-box: 90% of warrant quotes are exact substrings — the checker passes those, rejects the 10%.** Field separation (resolved): the **warrant is the verbatim span** (checkable); the **claim text is normalized** (never substring-matched against source).

**Concrete.** Fail-fast lint stage in the plugin; reject any edge lacking a correct warrant. Offline causal-faithfulness counterfactual (decoy-source re-citation → low-confidence — Wallat 2024).

### 3.3 Epistemic status as first-class claim data — **Amend ADR-56 (built uncertainty-flag); shape ADR-90, ADR-52, ADR-50**

**What.** Every claim/relation carries: uncertainty flag, source-span provenance grade (complete/partial/broken), two-axis confidence, source-document-type **[paper-only]** (review/primary/preprint) + evidence-strength, a `source_anchor`. Contradiction/supersession privilege primary evidence over echoed consensus.

**Why.** LM fluency is not knowledge (Bender 2021). The uncertainty flag + provenance grade + source-type ship now (they serve the high-cost faithfulness tier, §0e/§3.2); the heavier `(context, variables, relationship)` decomposition is only needed by §3.1's **deferred** NLI gate, so build that slice only if/when that gate is. **Version-pin epistemic metadata** to model + prompt — *more* important with an API the provider silently updates. Self-consistency can feed uncertainty, but **only on closed-label steps** and at API cost (§3.6).

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

**Removal is a decision held to the same evidential bar as addition.** A drop on n=6–8 fixtures is no more certain than an *add* on them — at n=6 you cannot tell 100% from 70%. Each item below is tagged **[architecture]** (grounded in a structural fact — solid) or **[provisional, n≈6]** (grounded in a smoke test — re-confirm in-domain before treating as settled).

- **QLoRA fine-tuning** — **[architecture]** the live engine is an API (not fine-tuneable); the n=6 result only corroborates (§3.6).
- **High-precision contradiction engine for alpha.9** — **[architecture/error-cost]** deferred by §0e (the miss is low-cost), not by a measurement — solid as a *priority* call; the NLI numbers behind it are themselves [provisional, n≈6].
- **Holistic LLM "same variable?" gate** — **[provisional, n≈6]** recall 1/6 on the fixture; directionally clear but re-confirm. Decomposed if ever built.
- **"NLI cleanly replaces cosine"** — **[provisional, n≈6]** + literature (BRIGHT negation-blindness corroborates); cosine stays as qmd's retriever regardless.
- **Greenfield retriever / clustering stack** — **[architecture]** `qmd` and `cluster_mcp` already exist; these are deltas (§4.1/§4.2).
- **Blanket self-consistency** — **[architecture]** an API per-token bill now; reserve for genuine uncertainty (§3.6).
- **Atomic-as-stored-unit** / **typed graph "at scale"** / **"least-privilege is sufficient"** / **per-item gate** — **[warning, §0b]** narrowed on *others'* measurements, not ours — provisional until in-domain.

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
| Amend (built) | 09, 10 | §3.1 contradiction **soft-flag** (NLI/gate apparatus deferred by §0e) | ship soft-flag; NLI deferred |
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
