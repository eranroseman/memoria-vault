# Archive → specs gap analysis (of record)

Date: 2026-07-12. Status: **analysis of record + routing.** A full gap analysis
of `design-history/archive/releases/0.1.0-beta.1/` (53 files, ~2.5 MB) against
the live `docs/superpowers/specs/` corpus, by 8 parallel cluster readers each
classifying content as CAPTURED / MATERIAL-GAP / HISTORICAL against the
consolidation (`2026-07-12-beta.1-consolidation.md`).

## Meta-finding

The archive is **~95% correctly historical** and stays frozen as-is (the
MANIFEST curation holds; nothing moves *out* of it). `main`'s beta.1 restarted
from the alpha.20 code baseline, so the entire alpha.15→beta.1 adjudication
layer verifies against a design that no longer exists and surfaced **zero** live
code gaps. The residue below is ~30 decisions/constraints that were specified in
the 2026-07-03/05 work, never reached `main`, and are still relevant — they are
**promotions into the live specs**, not reasons to keep the archive differently.
Two dominant losses: a **content-security/egress layer** (→ its own spec) and
the **2026-07-04 evaluation apparatus** (→ empirical-use plan / I1).

## Owner decisions (2026-07-12)

- **Reranker (flag 1) — RESOLVED.** `reranking (CPU cross-encoder, per-group)`
  is **not** adopted as a beta.1 default. Research: Memoria is *both*
  small-corpus per query (skip-first territory) *and* reasoning-intensive
  (where local CPU cross-encoders **degrade** — BRIGHT / Su et al. 2025 —
  and stronger LLMs help most); neutral guidance is "measure with/without, skip
  if ≤0"; and a rerank default collides with the BM25-until-a-spike-beats-it
  doctrine. **Adopt:** reranking **off by default**, fixture-gated exactly like
  dense retrieval (R3 spike decides none / LLM / cross-encoder over the real gold
  set, incumbent-until-beaten). If it earns in, reasoning-grounding queries get
  **LLM-listwise (priced)** reranking; a CPU cross-encoder is admissible only for
  non-reasoning targeted (Shape-1) lookups and only if it beats no-rerank without
  regressing reasoning-query grounding. → consolidation R2 updated.
- **Engine-projected argument canvas (flag 2) — KEEP as beta.1** (owner ruling).
  No change; the rejection rationale (no-measured-demand / feasibility-gate) is
  noted and overruled on merit.
- **Hub (M1) — ADOPT as beta.1: the wiki↔ZK bridge, dual-nature.** The hub is
  **both** a human-created editorial concept **and** part of the wiki LLM-digest
  process — the master-pattern cut applied to the organizing layer. Human half:
  a curated link-list over works/notes with human-owned inclusion and ordering.
  Digest/wiki half: a machine-appended, run-attributed, **revertible Candidates
  block** that never reorders the curated body; `digest→hub` membership offered
  as a candidates *affordance* on digestion (not a hard per-import terminus); and
  a deterministic machine-maintained "Related works" section on digests (top-k by
  shared references / co-citation) so the compounding-wiki bet compounds.
  Suggestion/staleness tooling is post-beta, size-gated. → new consolidation
  unit **S3**.
- **Content-security layer — ADOPT as a spec:**
  `2026-07-12-beta.1-content-security.md` (CS1–CS8).

## Routing table — material gaps → target

Severity: ⬆ high · ◾ medium · 🔹 low/confirm. "Target" is the package
(consolidation §2) or spec that now owns the item.

| # | Gap | Sev | Target |
|---|---|---|---|
| 1 | Exfiltration linter (content-layer neutralization, apply+export) — live requirement, absent in code | ⬆ | **content-security CS1** (alpha.21) |
| 2 | Renderer-side beacon neutralization of machine-written text | ⬆ | content-security CS2 (U3) |
| 3 | Out-of-band change witness (foreign human-file edits; restriction-key-removal fails open) — 3-reader | ⬆ | content-security CS3 (alpha.21, beside F2) |
| 4 | Import nominate-vs-author zero-LLM injection defense (fuzzy ≥0.95, SBMV, GROBID out) | ◾ | content-security CS4 (O2) |
| 5 | Enrichment metadata as injection channel (fenced data + instruction-likeness flag) | ◾ | content-security CS5 (X1) |
| 6 | Anti-laundering `unauthored` flag on promote-to-note | ◾ | content-security CS6 (W2) |
| 7 | `local-only` fail-closed egress/privacy marker; `bibliography.bib` never local-only | ◾ | content-security CS7 |
| 8 | Secret **read**-denylist for sandbox | ◾ | content-security CS8 → **beta.2-scope §3** |
| 9 | Vigilance-independent-defense trust rule (safety never credited to human noticing a marker) | ◾ | content-security (trust rule) + requirements Trust scope |
| 10 | `mc` provenance integrity: DB-authoritative + block-text-hash-bound; demote on file-only rebuild/human-edit-under-marker | ⬆ | **F1/F2** (alpha.21); refines design §4.0 |
| 11 | NLI launch-blocking calibration gate (seed the two measured failure classes + HANS/PAWS reversal probe) | ⬆ | **S2** + add to requirements §8.1.1 checks-before-implementation |
| 12 | Statement-conversion + multi-anchor/FEVER entailment; "mentions" = unknown stance | ◾ | S2 |
| 13 | Verification-gate risks: precision-only rewards abstention; string-match false-negatives on paraphrase | ◾ | **V1** |
| 14 | Retrieval honesty: empty="nothing matched over N docs"; truncated/abstract-only = suspect denominator; second-hop; year-spread flag; contrasts="contradictions within retrieved set", empty≠absence | ◾ | **R2** (`search-honesty`/`gap-visibility`) |
| 15 | Three-valued enrichment fields (`present\|absent-in-source\|not-yet-fetched`) + dual-denominator "unknown band" | ◾ | R2 + S-schema |
| 16 | Reject→fixture ratchet (disposition → eval gold set) | ⬆ | **E1 + I1** (closes the loop) |
| 17 | Concrete pre-registered retrieval-spike protocol (BM25 gold-set baseline, k=3 recall, `--substrate bm25+dense`) | ◾ | **R3** — use the frozen `retrieval-fusion-spike-protocol.md` as the starting draft |
| 18 | Supersession/retraction **consumption** (retrieval default-excludes superseded + FAMA resurface probe + successor pointer + Crossref sweep) | ◾ | **V1/O2** (only export-refusal captured) |
| 19 | Retraction-Watch flag-at-import + periodic re-check (banner, never delete) | ◾ | O2 / X1 |
| 20 | Preprint↔published as one work with versions; dedupe checks both ids | ◾ | O2 / G3 |
| 21 | Extraction-coherence gate (fail-closed) + ingest dead-letter stub (no source silently lost) | ◾ | O2 |
| 22 | memoriad job contract (idempotency keys, bounded retries→visible state, heartbeat-on-clean, jobs-produce-logs-only) | 🔹 | O2 / I1 (relevant when the scheduler lands, beta.2) |
| 23 | Citekey pinned/frozen at import; correction = revertible rename; conflicts flag never silent-merge | ◾ | O2 / G3 |
| 24 | MASSW 5-aspect digest schema (fixed `digest.md` headings) + recursive batch-condense + staged relevance + printed sources-used denominator | ◾ | W1/W2 (digest engine spec) |
| 25 | Per-class body-section contract (`digest.md` headings; `project.md` mapped-claim delimiting the export gate consumes) | ◾ | S1 / C1 / V1 |
| 26 | Local-first ops playbook parameters (snapshot-before-migration/import + retention; verify-by-restore; SQLite hot-copy via VACUUM INTO/backup-API never cp; DB outside synced tree + rebuildable; migration runner numbered/transactional/forward-only) | ◾ | **F3/K3/G1** (alpha.21) |
| 27 | Exploration-channel **surfacing** doctrine (salient, labeled, interpretable, consider-the-contrary) | ◾ | R2 / U-surfaces (algorithm captured, placement not) |
| 28 | PMC bulk-access transition: classic FTP deprecated → **PMC Cloud, removal ~Aug 2026**; DOAJ/S2ORC unevaluated | 🔹 time-sensitive | **O1** seed-corpus |

### Evaluation apparatus (2026-07-04 `evaluation-protocol`, dropped wholesale) → empirical-use-action-plan / I1

| # | Gap | Sev |
|---|---|---|
| E-a | Gate-efficacy causal protocol: ABAB/multiple-baseline reversal (≥3×, ≥5 obs/phase) + both-directions re-judging (automation-bias flip rate) + approved-error/false-reject "is-review-theater" | ⬆ |
| E-b | Weekly sampled citation audit (recall/precision, oversample near-threshold NLI + truncated/abstract-only) | ◾ |
| E-c | Decoy re-citation probe (plant already-cited span in decoy; re-citing exposes surface-matching-as-grounding) | ◾ |
| E-d | Relegation-cluster leading indicator (empty/failed Asks → capture-only) ahead of the 14-day abandonment trigger | ◾ |
| E-e | Anytime-valid / e-value verdict statistics (weekly peeks = optional stopping) | ◾ |
| E-f | Paired same-day-ChatGPT counterfactual procedure (archive answer before reading Memoria's) | ◾ |
| E-g | Non-backfillable day-1 signals beyond generic disposition-capture: reversal stamped at event-time, reviewer decision-time, deny-reasons, accept-unedited-vs-after-edit | ⬆ |
| E-h | Two-sided disposition-rate bands (≳90% rubber-stamp / ≲20% mistuned) + supervision-budget arithmetic (realistic annual labels before adding any calibratable threshold) | ◾ |

### Deferred → `0.1.0-beta.2-scope.md`

- Secret read-denylist (#8, into §3 code-exec).
- Discovery honesty contract (echo-chamber/paired-channel, PRISMA-S per-run log, index-relative saturation + signed stopping rule) — *if* any snowball/citation-monitor ships; discovery is otherwise beta.2 (autoresearch).
- Named revive triggers for Semantic Scholar + a topics/facet tier (enumerate in beta.2-scope's activation rules).

### Confirmed HISTORICAL (stays archived — do not carry forward)

The six alpha.15 gap-analysis files, S01–S16, the 1,680-line adjudication, the
redo borrow/adapt/reject ledgers, the clean-slate 07-03 design's resident-daemon
host model + VS Code appendix, `memoria.stages` YAML pipeline state, vault entity
pages, BBT-export-as-bibliography-of-record, and the rejected alternatives. All
verified superseded by the alpha.20 restart or endorsed drops; the *decisions*
they produced are on `main`, the *evidence* is correctly archive-only per the
owner's "prior ADRs/designs are reference, never justification" ruling.

## Watch-items (confirm, likely moot)

- `project.md` claim-delimitation contract — likely satisfied by the built
  writing pipeline + verify/export gate; confirm the contract exists in C1/V2.
- "Memoria-born vault, never nested in an existing vault" — implicit via
  `memoria init` + K1 detachability; explicit statement absent.

## Disposition of the archive itself

Stays frozen under `design-history/archive/`. This document is the durable
record that its *live* content has been promoted; the archive remains the
evidentiary backstop (full snapshot in tag `archive/scratch-final`).

## Sources (reranker research)

- [Choosing a reranking model, 2025-26 (ZeroEntropy)](https://zeroentropy.dev/articles/ultimate-guide-to-choosing-the-best-reranking-model-in-2025/)
- [ReRank or Not — when to rerank in RAG](https://medium.com/@sindhuja.codes/when-to-rerank-and-when-to-let-semantic-search-do-its-job-af3adddd602b)
- [Does reranking improve your RAG (particula.tech)](https://particula.tech/blog/reranking-rag-when-you-need-it)
- [ReasonRank: reasoning-intensive passage ranking](https://arxiv.org/pdf/2508.07050)
