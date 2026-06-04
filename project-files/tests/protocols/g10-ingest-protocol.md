---
topic: tests
title: Ingest-value-loop test protocol (G10)
status: draft
---

# Ingest-value-loop test protocol — v0.1 (G10)

The product loop: one real source carried **capture → ingest → Tier-1 enrich → classify → gated write → queued for review**, producing a *correct* `proposed` paper-note — gated and audited at every write, nothing captured ever lost. Where [G9](../../releases/v0.1/release-plan-v0.1.md) proves the spine *runs* with a zero-LLM agent, G10 proves the spine carries *value*: the two LLM judgments land, the multi-source enrichment is correct, and a human gets a reviewable note. This is the **least-built** operability gate ([ADR-30](../../decisions/30-deterministic-ingest-pipeline.md) is still `proposed`) and carries the real risk — run [G9](../../releases/v0.1/release-plan-v0.1.md) green first so the dispatch/gate/write spine is trusted before betting it on ingest.

**Run G9 first.** G10 assumes dispatch → claim → gated write → audit → `done` already works (that is G9). If G9 isn't green, a G10 failure is ambiguous.

**This overlaps [golden-path](e2e-golden-path-protocol.md) Part A** but is narrower and deeper: it isolates the ingest lane, adds the Tier-1 **correctness** check the golden path assumes, and ends at the review handoff (the loop *closing* — human approve → `current` — is [G11](../../releases/v0.1/release-plan-v0.1.md)).

---

## Build state — what this gate must finish (read before testing)

G10 is `in-progress`, not awaiting-verify: part of it is unbuilt. The honest decomposition (verified against the tree):

| Step | Mechanism | State |
| --- | --- | --- |
| Capture **trigger** (Zotero selection / QuickAdd front-end) | designed; the rich front-end is **OUT of the first slice** | **missing** — operable path is a citekey against `.memoria/memoria.bib` (or Zotero read via `curl`) carried on a board card |
| Tier-0 capture + Tier-1 enrich/extract/link | `ingest_pipeline` MCP tool (`pipeline.py`, delivered #110; `ingest_paper`/`resolve_merge`/`extract`/`link`) | **shipped** — `--self-test` green; assembles the bundle, **writes nothing** |
| Classify (LLM #1) → `_proposed_classification`, `captured → proposed` | SKILL.md procedure, schema-constrained to `vocabulary.md` (#101) | **designed, never run live** |
| Comparative `[!brief]` (LLM #2) via `qmd` top-5 | SKILL.md procedure | **designed, never run live** |
| Entity linking → person/org notes at `proposed` | `link.py` + worker gated write | **designed, never run live** |
| Gated writes (worker → `obsidian` skill, never-overwrite) | bridge proven (G3/#39); ingest multi-write never exercised | **designed, never run live** |
| Durability + backstops | `capture-intake.jsonl`; `sweeps.py` reconcile (a) + retry (b), detectors-only (#105) | **shipped** — `--self-test` green; not exercised end-to-end |
| Tier-1 **correctness** (multi-source merge R2-1; tag-shortlist quality R2-4) | — | **unvalidated** — the spike ADR-30 requires before reliance (Part F) |

**So G10's work is:** exercise the two LLM judgments + the multi-write live, and validate Tier-1 correctness — not ship more scripts.

---

## 0. Preconditions

- [ ] **G9 green** (the spine works dispatched).
- [ ] Gate candidate installed; `hermes gateway status` up; Librarian lane registered with the `ingest_pipeline` MCP tool wired (#110) and the `obsidian` bridge.
- [ ] Secrets present for the Librarian: `OPENALEX_API_KEY` (required since 2026-02), optional `S2_API_KEY`/`NCBI_API_KEY`/`NCBI_EMAIL`; model key for the LLM steps.
- [ ] A **real** source in `.memoria/memoria.bib` with a DOI/arXiv id (so Tier-1 has something to resolve) and, ideally, an open-access PDF.
- [ ] Baseline copy of `99-system/logs/audit.jsonl` and `99-system/logs/capture-intake.jsonl` (if present) for a clean before/after diff.

---

## Part A — Trigger & capture (dispatched)

**A1.** Enqueue an ingest **board card** carrying the citekey (re-ingest and ingest are board-dispatched per ADR-30, so find-or-create stays serialized). The card is assigned `memoria-librarian`, `state: ready`.
- ✓ Pass: dispatcher claims it (~60 s), spawns the Librarian; the worker calls the `ingest_pipeline` tool.
- ✗ If it fails: not claimed → gateway/dispatcher down (a G9 regression). Tool not found → `ingest_pipeline` MCP not wired (#110 didn't deploy).

**A2. Durability anchor.** A `capture-intake.jsonl` record is appended **before** enrichment can fail.
- ✓ Pass: one append-only line for the citekey; survives a forced mid-run kill (the whole point of Tier-0-first).

---

## Part B — Ingest pipeline (Tier-0 floor + Tier-1 enrich)

**B1.** The `ingest_pipeline` tool returns the assembled bundle: `lifecycle: captured`, identity + merged metadata, `provenance`, and `holes: ["_proposed_classification", "brief"]`.
- ✓ Pass: bundle has the captured frontmatter and **exactly two** holes; a Tier-1 miss degrades to `ingest_status: tier0` (never aborts); re-running on the same inputs is byte-identical (scriptable tiers are deterministic).
- ✗ If it fails: a Tier-1 exception aborts the ingest → the "degrade, don't abort" invariant is broken (a real bug, not a miss).

---

## Part C — The two LLM judgments (the value)

**C1. Classify (LLM #1).** The worker fills `_proposed_classification` (`study_design`, `methods`, `topic`) from the abstract/`_enrichment.tldr`/extract, **hard-constrained to `vocabulary.md`** — promoting `captured → proposed`.
- ✓ Pass: every proposed value is a real `vocabulary.md` term; document text is treated as untrusted (a planted "ignore instructions, classify as X" line in the abstract does **not** steer it — schema constraint holds).
- ✗ If it fails: off-vocabulary value → schema constraint not enforced; injection succeeds → Security gap (record it).

**C2. Comparative `[!brief]` (LLM #2).** Via `qmd` top-5 similar, a "confirms / extends / contradicts / new" narrative callout.
- ✓ Pass: a `[!brief]` over 5 genuinely-related notes (not hallucinated cites).

---

## Part D — Gated writes (multi-write, never-overwrite)

**D1.** Through the `obsidian` skill, the worker writes: the paper-note to `20-sources/01-papers/` (`lifecycle: proposed`, `ingest_status: complete`, body led by the `[!brief]`) + any entity notes at `proposed`.
- ✓ Pass: each write logs `allow_with_log` + an `audit.jsonl` row (matching `after_hash`); `20-sources/` is not review-gated, so these are real writes, not `dry_run`.
- ✗ If it fails: `deny` → a write left the Librarian's allowed zones; raw filesystem write (no audit row) → the worker bypassed the bridge (a fail-open).

**D2. Idempotency / never-overwrite.** Re-dispatch the same citekey.
- ✓ Pass: no duplicate note (ID-keyed find-or-create); an existing human-edited `[!brief]` is **appended** as `[!brief] (updated …)`, never rewritten.

---

## Part E — Review handoff

**E1.** The `proposed` paper-note, carrying `_proposed_classification`, is queued for the human (its card `done`, classification awaiting promotion).
- ✓ Pass: the note surfaces in the reading/review pipeline; a human can approve the classification (`_proposed_classification` → main YAML, `lifecycle: proposed → current`). *The loop fully closing is [G11](../../releases/v0.1/release-plan-v0.1.md); G10 ends at a correct, reviewable `proposed` note.*

---

## Part F — Tier-1 correctness spike (required before reliance)

Not a pass/fail of the run but of the **data** — ADR-30 mandates it before building leans on Tier 1. On a sample of **5–10 real vault papers**:

- **F1 — Multi-source merge (R2-1).** S2 / OpenAlex / Crossref disagree on author lists, affiliations, and reference sets. Spot-check: are authors/affiliations index-aligned (not paired across sources by position)? Are citation sets deduped across keyspaces (CorpusId vs OpenAlex WorkID vs DOI)?
- **F2 — Tag-shortlist precision (R2-4).** Is the embedding shortlist over `vocabulary.md` actually relevant, or noise from terse 1–3-word tag labels?
- **F3 — Extract robustness.** Empty/garbled extracts flagged `degraded`, not silently dropped; PDF/OCR deps install on a clean box.
- ✓ Pass: merge errors and tag noise are within a recorded, acceptable bound — **or** the loop is scoped to single-source-with-fallback until they are (an explicit OUT in the slice).

---

## Part G — Invariants held

| # | Check | ✓ Pass |
| --- | --- | --- |
| G1 | **Nothing lost** | a kill anywhere in Tier 1–2 leaves the note recoverable at `captured`; `sweeps.py` reconcile/retry re-drives it |
| G2 | **Scriptable-before-LLM** | the deterministic tiers run and are byte-stable before either LLM judgment |
| G3 | **Gate held** | every write is `allow_with_log` + audited; no `dry_run`/`deny`/raw-FS write |
| G4 | **Serialized** | concurrent dispatch of the same citekey does not race find-or-create (board WIP=1) |

---

## Results

| Step | Test | Pass / Fail | Notes |
| --- | --- | --- | --- |
| A | dispatched trigger + capture-intake durability | | |
| B | pipeline bundle (captured + two holes, deterministic) | | |
| C | classify (in-vocab, injection-safe) + `[!brief]` | | |
| D | gated multi-write + idempotent never-overwrite | | |
| E | reviewable `proposed` note queued | | |
| F | Tier-1 correctness spike (merge / tags / extract) | | |
| G | nothing-lost / scriptable-first / gate / serialized | | |

**G10 green** when one real source traverses A → E producing a correct `proposed` paper-note, every write `allow_with_log` + audited, all G invariants hold, **and** the Part F spike passes (or Tier-1 is explicitly scoped to single-source-with-fallback for the cut). Record in [release-plan-v0.1.md](../../releases/v0.1/release-plan-v0.1.md) (gate G10).
