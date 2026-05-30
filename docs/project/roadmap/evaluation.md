---
topic: roadmap
---

# Evaluation and benchmark-informed design

## Purpose

A review of ~51 agent / research / memory benchmarks (the full capability-mapped taxonomy is at [evaluation-benchmarks.md](evaluation-benchmarks.md)) produced two things: an **evaluation program** for Memoria, and a short list of **design implications**. This document is the roadmap-level synthesis — what to measure, how, and the design implications the literature actually warrants: one structural change, two refinements, and a set of observability additions. The headline is that the research **validates** most of the design; the changes are few and targeted.

## How Memoria is evaluated — two layers

**Layer 1 — vault-native gold eval (primary).** Off-the-shelf benchmarks measure the *model* on someone else's corpus; they do not answer Memoria's real question — *does this vault compound?* The primary eval is a small, hand-curated gold set drawn from the actual vault (the `vault-eval` harness; see [ADR-23](../decisions/23-vault-eval-integration.md)): ~20 items per workflow (`find`, `verify`, `query`, `classify`, `distill`, drift), re-run quarterly. The **trend** is the signal, and the metrics feed the existing [success-metrics.md](success-metrics.md) diagnostics — they are diagnostic, not contract, and must not become optimization targets.

**Layer 2 — external benchmarks (reference).** The full capability-mapped taxonomy is at [evaluation-benchmarks.md](evaluation-benchmarks.md); the condensed map below is the quick reference. Each benchmark is tagged by **adoption mode**:

- **run** — run the harness as-is for a capability baseline (e.g., LongMemEval, CiteME, τ-bench, BRIGHT, AgentDojo).
- **borrow** — adopt the *metric or task*, don't run the leaderboard (e.g., **FAMA** for drift, **pass^k** for lane reliability, **coverage@k** for loose-ends, Contradiction-Retrieval for the contradictions surface, MASSW's 5-aspect note schema).
- **validate** — design/positioning evidence; cite, don't run.

Roughly half are `run`, about a third `borrow`, the rest `validate` — i.e. most of this corpus is to be **learned from**, not run.

**Condensed adoption map** (one row per Memoria surface; the workspace taxonomy has the full per-benchmark detail):

| Surface / capability | Benchmark(s) | Mode |
| --- | --- | --- |
| Find / retrieval | LitSearch, BRIGHT | run |
| Classify & organize | ResearchArena | run |
| Query / corpus QA | PaperQA · LitQA; KnowledgeBerg | run; borrow (coverage@k) |
| Verify / citation | CiteME, CiteGuard; Wallat (correctness ≠ faithfulness) | run; borrow (NLI support check) |
| Write & revise | ALCE, ExpertQA; EditEval, IteraTeR | run; borrow (edit-intention) |
| Memory & drift | LongMemEval, MemoryAgentBench; Memora, ClawArena | run; borrow (FAMA, CRS) |
| Tool use & RPC | τ-bench; ToolLLM, API-Bank | run; borrow (pass^k) |
| Safety / injection | AgentDojo, InjecAgent, ToolEmu | run |

Deliberately **out of scope** (and tracked as such in the workspace taxonomy): autonomous-scientist / end-to-end discovery, hypothesis & novelty scoring, Deep-Research report generation, and model-weight knowledge-editing — each conflicts with Memoria's human-gated, corpus-curating, file-based posture.

## Integrating vault-eval into the runtime

`vault-eval` graduates into the runtime rather than staying an external script, reusing existing machinery (decision recorded in [ADR-23](../decisions/23-vault-eval-integration.md)):

- **Vault:** gold tasks live in `00-meta/05-eval/`; results append to `00-meta/08-metrics/eval/`; the Linter's broken-link detector guards gold-item target paths. (These directories will be created on first eval run; pre-create with `.keep` stubs if running evaluation scripts manually.)
- **Workers:** the board dispatches a scheduled `eval` card (quarterly + on-demand, like the discovery loop); workflow profiles execute each gold task via their real commands (`verify`-eval reuses the Verifier's `cite-check`); eval-context writes are non-committing, Policy-MCP-scoped to a scratch path; the Linter scores and records the verdict.
- **Observability:** per-workflow scores trend in `00-meta/08-metrics/` and surface on a dashboard — **diagnostic, not gating** (unlike `drift-watch`'s structural FAIL).

## Design implications

### Confirmed by the research — no change

The strongest single result of the review. Each is external evidence that an existing decision is correct:

- **Deterministic Zotero / Better BibTeX ingest.** Even search-enabled frontier models produce ~50.9% fully-correct BibTeX; deterministic identifier resolution reaches ~91.5% (Rao 2026). Confirms "[Zotero is the source of truth](../../reference/frontmatter-schema.md)" — keep LLMs out of metadata construction.
- **The blocking human gate / L3 ceiling.** Cornelio 2025 ("verification bottleneck"), Bisht 2026 ("co-scientists, not autonomous scientists"), and an independently-built human-in-the-loop closed-loop system (Jacobson 2026) all converge on Memoria's posture.
- **Narrow per-lane profiles.** Function-calling degrades as the toolkit grows (Rabinovich 2025) and tool *retrieval* is itself a weak link (ToolRet 2025) — both argue for compact per-lane permissions.
- **Vault-as-distilled-memory / thin control over thick state.** MemoryAgentBench ("memory ≠ long context; it is a distilled, incremental representation") and the Externalization survey restate the architecture directly.
- **No LLM-judged contradictions.** Memory-agent benchmarks show LLM memory/similarity judgments are unreliable — validating [ADR-16](../decisions/16-contradictions-dashboard.md)'s rejection of LLM-judged tensions in favor of human-set typed relations.

### Change 1 (proposed) — claim *supersession* as a first-class relation

**The gap.** The schema expresses how *developed* a claim is (`maturity`) and how *durable* a note is (`lifecycle`), but nothing expresses that a claim was **overturned by a newer one**. An `evergreen` claim a later paper just invalidated is structurally indistinguishable from one that still holds. [`contradicts`](../decisions/09-typed-relations-frontmatter.md) (two claims disagree) is not the same as *supersedes* (B replaces A as the current belief over time); [drift-watch](../../explanation/dashboards/drift-watch.md) covers *structural* drift, not claim staleness; and [ADR-16](../decisions/16-contradictions-dashboard.md) is deferred.

**The evidence.** Reusing a superseded fact is exactly the failure mode **Memora's FAMA** metric was built to catch, and **ClawArena**'s "revise, don't accumulate" names it. These also show supersession is the *least reliably automatable* memory capability — which means it must be carried by **structure** (human-set, agent-maintained), not inference. That is precisely Memoria's founding thesis: *bookkeeping, not intelligence*.

**The move.** Extend the `supersedes` / `superseded_by` pattern **already used for ADRs** to claim-notes, plus a queryable validity flag distinct from `maturity`. This lets `query`/`write` filter superseded claims by structure and enables a FAMA-style Linter check. Captured as [**ADR-22: claim supersession relation**](../decisions/22-claim-supersession.md); it also re-weighted the priority of [ADR-9](../decisions/09-typed-relations-frontmatter.md) / [ADR-16](../decisions/16-contradictions-dashboard.md), both now **accepted** (the `relations:` namespace and the contradictions dashboard) — supersession was the correctness-critical carve-out, with the NLI contradiction-proposer left as future work.

### Refinement 2 — an entailment check in `verify`

[Verify](../../how-to/workflows/downstream/verify.md) traces a draft claim to a claim note via citekey lookup + similarity search. Wallat 2024 (correctness ≠ plausibility; CiteME: embeddings score 0%) shows a *similar* note is not necessarily a *supporting* one. Add a support/entailment step on the matched note — a tightening of the existing deterministic + LLM-on-the-ambiguous-band hybrid, not a new mechanism.

### Refinement 3 — reasoning-augmented `query` / concept-`find`

[Find](../../how-to/workflows/upstream/find.md)'s citation-graph discovery is well-grounded, but concept-search and vault querying should add a **query-rewrite/decomposition** step and keep a **hybrid keyword + dense** retriever. BRIGHT shows query-side reasoning adds large gains and plain embeddings fail on reasoning-relevant queries; ResearchArena (BM25 wins broad organize) vs LitSearch (dense+rerank wins focused search) shows the two retrievers are complementary.

## Sequencing

1. **Now.** Stand up `vault-eval` on `find` + `verify` (highest-signal surfaces), and start logging suggestion-disposition + per-run cost (see **Observability** below — these cannot be backfilled).
2. **Next.** [ADR-22 (claim supersession)](../decisions/22-claim-supersession.md) — the one structural change (drafted; pending acceptance).
3. **Then.** The two refinements (verify entailment; query rewrite).
4. **Ongoing.** Run the `run`-mode benchmarks as capability baselines; fold `borrow`-mode metrics (FAMA, pass^k, coverage@k) into `vault-eval`.

## Observability — what to log, measure, and surface

> [success-metrics.md](success-metrics.md) is the canonical home for the metric *definitions*; this section specifies only the eval-specific **logging** (what to capture from day one, and why), not a second definition of each metric.

The benchmark corpus is autonomous-agent-centric, so the signals that most determine Memoria's success are under-measured. The implication is mostly about **logging, not dashboards**: human-loop health and cost trends cannot be reconstructed retroactively, so capture them in the append-only event log (`00-meta/02-logs/audit.jsonl`; aggregates in `00-meta/08-metrics/`) from day one, and add dashboards over that log only when a question recurs (the [expansion-threshold rule](README.md#expansion-threshold-discipline)). All of it is diagnostic, not contract; any LLM-as-judge stays advisory.

**Log from day one (cheap; cannot be backfilled):**

- **Suggestion disposition (human-loop friction).** Record each proposal's `review_status` outcome — accepted / edited / rejected — per profile. The accept : edit : reject trend is the clearest signal of whether the human-AI loop is paying off; no benchmark measures it, and [success-metrics.md](success-metrics.md) tracks review *backlog*, not disposition.
- **Cost per run.** Tokens / $ per card-run, rolled up to cost-per-promoted-claim and the nightly discovery-loop trend. ScienceAgentBench shows capability gains can cost 10×, and unattended loops compound.
- **Claim-staleness / FAMA exposure** (with [ADR-22](../decisions/22-claim-supersession.md)). Count current claims carrying `superseded_by`, and — the real signal — drafts or answers that cite a superseded claim. This has no dashboard home: [drift-watch](../../explanation/dashboards/drift-watch.md) is *structural* drift and the [contradictions dashboard](../../explanation/dashboards/contradictions.md) (ADR-16) tracks *disagreement between current claims*, not *staleness*. Grounded in Memora (FAMA) and ClawArena.

**Refine existing dashboards:**

- **[fleet-health](../../explanation/dashboards/fleet-health.md) trust score → shape it like ClawArena's CRS** (completion × robustness, with success-cohesion / failure-dispersion) and track **pass^k** consistency rather than single-shot success — τ-bench shows reliability collapses across repeated runs (pass^1 ~61% → pass^8 ~25%) in a way a flat average hides.
- **[audit-log](../../explanation/dashboards/audit-log.md) → treat Policy-MCP denials / out-of-lane writes as a security signal**, with spike alerting. Memoria ingests untrusted PDFs (an indirect-prompt-injection surface — AgentDojo / InjecAgent ~24% success; ToolEmu: even "safe" agents act riskily ~24%), so a denial spike is an injection indicator, not just forensics.
- **`verify` → a provenance-health metric**: support-check failure rate + citation completeness (Citation Failure), plus a bibliographic-hallucination rate that should sit near zero — a live confirmation the deterministic-Zotero ingest is holding (Rao: search-enabled LLMs get ~50.9% of BibTeX fully right).
- **[weekly-review](../../explanation/dashboards/weekly-review.md) / loose-ends → a coverage@k angle**: surface *qualifying notes not yet linked or found*, beyond the orphan count (KnowledgeBerg; AutoResearchBench Wide-Research).

**The enabling change.** Extend the append-only event log so each run records **disposition, cost, tool-call outcome, and verify result** — not only *what changed*. Every metric above aggregates from that one substrate.

## Related

- [success-metrics.md](success-metrics.md) — the diagnostic metrics this program feeds.
- [ADR-9 typed relations](../decisions/09-typed-relations-frontmatter.md), [ADR-16 contradictions dashboard](../decisions/16-contradictions-dashboard.md) — now accepted; Change 1 re-weighted them ahead of adoption.
- [ADR-23 vault-eval as a maintenance capability](../decisions/23-vault-eval-integration.md) — how the harness lives in the runtime (Linter-owned, non-gating).
- [vault/frontmatter-schema.md](../../reference/frontmatter-schema.md) — where the supersession relation + validity flag would live.
- [workflows/downstream/verify.md](../../how-to/workflows/downstream/verify.md), [workflows/upstream/find.md](../../how-to/workflows/upstream/find.md) — targets of the two refinements.
- [architecture/why-no-autonomous-synthesis.md](../../explanation/architecture/why-no-autonomous-synthesis.md), [vision.md](../../explanation/vision.md) — the posture the research validates.
- [dashboards/drift-watch.md](../../explanation/dashboards/drift-watch.md), [dashboards/fleet-health.md](../../explanation/dashboards/fleet-health.md), [dashboards/audit-log.md](../../explanation/dashboards/audit-log.md), [dashboards/weekly-review.md](../../explanation/dashboards/weekly-review.md) — the surfaces the observability additions touch.
- [architecture/memory-tiers.md](../../explanation/architecture/memory-tiers.md) — the append-only vault audit memory (`00-meta/02-logs/`, `00-meta/08-metrics/`) the new telemetry extends.
- [evaluation-benchmarks.md](evaluation-benchmarks.md) — the full benchmark taxonomy (scoping principles, per-capability tables, minimal suite) this synthesizes.
