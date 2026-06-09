---
topic: explorations
title: Publication strategy — paths, shapes, and sequence
status: deferred
created: 2026-05-27
parent: Design notes
grand_parent: Explanation
nav_order: 20
nav_exclude: true
---

# Publication strategy — paths, shapes, and sequence

> **Path 1 is decided.** The recommendation distilled from this analysis — pursue the vault-eval / vault-CiteME benchmark first, and start the six-signal capture now — is adopted as [ADR-20](../adr/20-publication-path.md). This proposal is retained for the **deferred** parts: the full four-path comparison, the per-path work-breakdowns, and the negative space, which inform the *next* publication decision (Path 2 vs. Path 3) once Path 1 has produced data. It is the source analysis behind ADR-20, not a competing decision.

## What

A standing map of how Memoria could become a published contribution: the publication shapes the surrounding field uses, where Memoria sits against each, four concrete paths ordered by tractability (plus a higher-novelty framing of the first), and a horizon sequence. It exists so the choice of the *second* paper is made against a worked analysis rather than re-derived from scratch.

## Why

Memoria is, as of v0.1, a design artifact. No surveyed paper published on design alone — every one ran a system and measured something, shipped a benchmark, or organized the field. Choosing a publication shape is the unblocking move because it determines what gets built and instrumented, and in what order. ADR-20 commits to the first paper; this document preserves the menu for everything after it, so the post-Path-1 decision is grounded.

## Background — publication shapes in the surveyed field

The 20-paper system/method survey clusters into five shapes (a different corpus from the ~51-paper capability-benchmark review that the [Measurement, quality, and verification](measurement-and-verification.md) metrics draw on):

| Shape | Surveyed examples | Count |
| --- | --- | --- |
| System paper (working system + capability evaluation) | AI Scientist, AI-Researcher, Agent Laboratory, AI co-scientist, AgentRxiv, CORAL, AiScientist (Chen 2026), MLR-Copilot, MetaGPT, OpenHands, AutoGen, ResearchAgent | 12 |
| Benchmark paper (public benchmark + frontier-model evaluation) | LitSearch, CiteME, ResearchArena | 3 |
| Method paper (specific technical advance with measurement) | SciMON, MOOSE (Yang 2024), Qi 2023 | 3 |
| Survey (organize the field, name the patterns) | Gridach 2025 | 1 |
| Domain-adapted model paper | SciLitLLM | 1 |

Each shape has different evidence requirements; picking a shape decides what work needs doing.

## Where Memoria stands vs. each shape

| Shape | What it needs | What Memoria has | What's missing |
| --- | --- | --- | --- |
| System paper | Working impl + capability evaluation vs. baseline | Design only | Implementation, baseline comparison, metric |
| Benchmark paper | Public benchmark + frontier-model evaluation + dataset | A *designed harness* — [ADR-11 vault-eval](../adr/11-vault-eval-integration.md) + a CiteME-style fixture | Public artifact, frontier evals, release |
| Method paper | A specific technical advance with measurement | None claimed today | A measurable novel technique |
| Position / argument paper | A strong claim + supporting evidence + clear contrast | Strong design rationale | Empirical evidence, comparison data |
| Tools / artifact paper | Mature open-source repo + adoption | None public | All of it |

The design rationale already written is worth 30–50% of any of these — none ships without it, but none ships *with only* design either.

## The four paths

### Path 1 (most tractable, **decided — see ADR-20**) — vault-CiteME benchmark paper

**Claim.** "We introduce vault-CiteME, a within-corpus citation-attribution benchmark for AI research assistants, and evaluate N frontier models against the Memoria Verifier profile."

**Venue.** NeurIPS Datasets & Benchmarks Track; workshop tracks at ICLR / EMNLP for an earlier version.

**Why it's the lowest bar.** CiteME (Press 2024) was already accepted at NeurIPS D&B — a clear comparable. The contribution is the *within-vault* variant: bounded candidate space, different failure mode, different operator stakes than public-corpus attribution. Frontier LMs get 4–18% on public CiteME (tooled CiteAgent ~35%, see [Pattern provenance: borrow, adapt, ignore](../explanation/rationale/why-pattern-provenance.md)); the within-vault number is unknown, and that gap is the paper's empirical core. Comparables sharpened by the benchmark review: **CiteGuard** (retrieval-aware attribution; extends CiteME) and **Wallat 2024** (correctness ≠ faithfulness — a *similar* note is not a *supporting* one).

**Work required (~3–4 months part-time).**
1. Build a public 200-example vault-CiteME fixture (synthetic vaults or anonymized real-vault excerpts).
2. Evaluate 3–5 frontier models + 2 retrieval baselines.
3. Compare to public CiteME numbers to characterize the within-vault setting.
4. Release fixture + evaluation code + Memoria Verifier profile.

**What it would *not* claim.** That Memoria is the right design; that blocking review beats advisory; that single-user is the right scope. Those are deferred to later papers.

### Path 1′ (higher-novelty framing of Path 1) — vault-eval as the contribution

**Claim.** "We introduce *vault-eval*, a methodology and metric suite for measuring whether a curated, human-gated knowledge vault *compounds* — does the system find, verify, answer, and remember better on its own growing corpus over time? — instantiated on the Memoria vault across N workflows."

**Venue.** Same (NeurIPS D&B); the framing, not the venue, differs.

**Why it's more novel.** vault-CiteME is a CiteME variant — incremental by construction. vault-eval asks a question no benchmark in the ~51-paper review answers: not "how good is the model on a foreign corpus?" but "does *this* vault pay off as it grows?" It is system-level and corpus-native, adapting field-validated metrics into a PKM setting — FAMA (obsolete-memory reuse → claim staleness), coverage@k (loose ends), pass^k (lane reliability), CRS (completion × robustness), plus human-loop disposition (accept : edit : reject). The methodology + metric-adaptation *is* the contribution.

**The honest catch.** A benchmark paper needs a public artifact and a clean comparable; vault-eval has neither natively — its gold set is, by design, your private single-user vault, and there is no prior "does-the-vault-compound" number to beat. To publish it you must manufacture both: a released synthetic/anonymized gold vault others can run, and a defensible baseline (e.g., the same metrics on an untyped or advisory-review variant). Strictly more work than vault-CiteME.

**The resolution — not competing paths.** vault-CiteME is the tractable instance that grounds the methodology; vault-eval is the frame. The strongest single paper is "vault-eval, instantiated via two cells" — citation attribution (vault-CiteME) and claim staleness (FAMA exposure, [ADR-10](../adr/10-claim-supersession.md)) — shipped with a released synthetic gold vault. Choose **Path 1** to land a paper fast; choose **Path 1′** for the more cited, more defensible contribution if you can absorb the extra fixture work.

### Path 2 — System paper anchored on a specific capability

**Claim.** "Memoria: A vault-centered research operating system with structurally blocking human review. We demonstrate X% reduction in [specific operator pain point] compared to [baseline]."

**Venue.** CHI, CSCW, or UIST (HCI venues that take design-plus-evaluation); ACM Queue for a practitioner version.

**The hard problem.** Picking the right metric. Memoria's pitch is "bookkeeping, not intelligence" — the right comparison is *operator hours saved per unit of vault growth*, not *task accuracy*. That metric does not exist in the field; you would have to define and defend it.

**Work required (~6–9 months).**
1. Implement MVS + Librarian + Verifier + Linter (the minimum stack that demonstrates the blocking-review thesis, [ADR-03](../adr/03-structural-review-gate.md)).
2. Run 3 months of personal use with instrumented logging (the six-signal capture, now shipped — see [Telemetry & logs](../reference/telemetry.md)).
3. Run a 4–6 week comparison study — same vault, two operators, blocking vs. advisory review (or a generic-LLM-assistant baseline), see [ADR-41](../adr/41-configurable-review-gate-mode.md).
4. Quantify operator time-per-claim, false-promotion rate, vault link density, trust metrics over time.

**Risk.** n=1 or n=2 operator studies are publishable at CHI but draw skepticism; mitigated by detailed logging and qualitative methodology.

### Path 3 — Position paper + small empirical study

**Claim.** "Contemporary autonomous-research systems optimize for the wrong objective shape (scalar metrics, autonomous keep/revert, advisory review). We argue that for knowledge work, structural human-blocking review is the correct architectural commitment, and show [small empirical study] supporting the position."

**Venue.** TOCHI, ACM Queue, arXiv + a workshop; possibly CACM if the rhetoric is strong.

**Why it's harder than it looks.** Position papers without empirical work get rejected; with strong empirical work they compete with full system papers. The sweet spot is narrow.

**Strengths Memoria already has.** The "synthesis quality is not scalar" argument in [Why Memoria doesn't pursue full autonomy](../explanation/rationale/why-not-autonomous.md); the borrow / adapt / ignore table in [Pattern provenance: borrow, adapt, ignore](../explanation/rationale/why-pattern-provenance.md); the intellectual-foundations framing in [Intellectual foundations](../explanation/overview/intellectual-foundations.md). The benchmark review independently *validates* the core posture (deterministic ingest, blocking gate, narrow per-lane profiles, vault-as-distilled-memory) — the external corroboration a "this design is correct" claim needs.

**Work required (~9–12 months).**
1. Everything in Path 2 (you need the empirical evidence).
2. A formal field survey — largely satisfied by the ~51-paper capability-mapped taxonomy, which surfaces a distinctive finding: the long-term-memory benchmark cluster is citation-disconnected from the research-agent literature.
3. A "shape" comparison between Memoria and 3 reference systems (AI Scientist, Agent Laboratory, AI co-scientist) on common tasks where applicable.

### Path 4 (longest horizon) — Memoria as an open artifact

**Claim.** "We release Memoria, a vault-centered research OS, with documented evidence of N months of use across M researchers."

**Venue.** SoftwareX, JOSS, arXiv tools papers, or an HCI tools track.

**Why it's longest.** Requires a real implementation, adopter-facing docs, at least one external adopter, and time for adoption stories to accumulate.

**Strengths.** Integration with widely-used tools (Obsidian, Zotero, Hermes) is a real adoption asset; most surveyed systems are research code, where Memoria could be the operationally usable alternative.

## Negative space — what Memoria probably *cannot* publish on

Three superficially-attractive claims that would not survive review:

- **The seven-profile design alone.** MetaGPT, AI co-scientist, and Agent Laboratory already published multi-role architectures; Memoria's profile design is internally consistent but not novel enough to anchor a paper.
- **The Karpathy LLM-Wiki + Zettelkasten + Memex synthesis.** Argued in [Intellectual foundations](../explanation/overview/intellectual-foundations.md), but the three components are well-known; novelty has to be in what Memoria *does* with them.
- **Obsidian-as-substrate.** Many systems use Obsidian; operational, not contributory.

The novelty Memoria *can* claim is a triad plus the data payoff:
1. Policy-MCP-enforced zone permissions (per-folder write degradation, not per-agent prompt discipline).
2. Structurally blocking review state (`awaiting-review → approved` as a state machine, not an annotation).
3. Structural, human-set claim supersession ([ADR-10](../adr/10-claim-supersession.md)) as the dependable answer to the FAMA failure mode the memory-benchmark cluster shows is least reliably automatable.
4. Measurable consequences for knowledge-work outcomes — the part that requires the data every path routes through.

The first three are present in the design today; the fourth is what every publication path needs.

## Sequence

| Horizon | Action | Output |
| --- | --- | --- |
| This month | Start instrumented MVS use (six-signal capture) | Baseline time-series begins |
| Months 1–4 | Path 1: vault-CiteME / vault-eval benchmark | Workshop or NeurIPS D&B submission |
| Months 4–9 | Continue instrumented use; build Verifier + Librarian fully | 6 months of operator data |
| Months 9–15 | Path 2 or Path 3 (whichever the data supports) | CHI / CSCW / TOCHI submission |
| Beyond | Path 4: open-artifact release | JOSS / SoftwareX, external adoption |

The binding constraint is whether instrumented use starts now or in six months; a six-month delay pushes everything else proportionally.

## Trade-offs

The whole strategy is calendar-bound: publications need time series, not snapshots, and the un-backfillable signals (disposition, decision time) are lost forever if capture lags. The benchmark-first ordering trades the higher novelty of a position/system paper for tractability and de-risking — if within-vault citation numbers come out worse than public CiteME, the Verifier-as-gate thesis weakens, and it is better to learn that before staking a larger paper on it.

## Adoption trigger

This is a strategy document, not a buildable capability, so its "adoption" is the *next* paper decision rather than a feature schedule. Revisit to choose Path 2 vs. Path 3 once **Path 1 has landed and ≥ 6 months of six-signal operator data has accumulated** — the point at which the data, not the analysis, becomes the binding input.

## Guard

Do not commit to Path 2 or Path 3 before Path 1's data exists. Both depend on empirical evidence that only accumulates with instrumented use; choosing between them early means choosing on the strength of the argument rather than the data, which is exactly the failure mode the benchmark-first sequence is designed to avoid.

## Dependencies

- [ADR-20](../adr/20-publication-path.md) (the committed first paper this analysis sits behind).
- [ADR-11 vault-eval](../adr/11-vault-eval-integration.md) (the eval program Path 1/1′ instantiate); [ADR-10 claim supersession](../adr/10-claim-supersession.md) (the FAMA cell).
- The six-signal capture ([Telemetry & logs](../reference/telemetry.md)) running on the board-export cron (Phase 1 in the [timeline](../../project/release/v0.1/release-plan-v0.1-appendix.md)) — without populated logs, Paths 2/3 have no data.
- [ADR-41](../adr/41-configurable-review-gate-mode.md) (the comparison arm for the Path 2/3 study); [Measurement, quality, and verification](measurement-and-verification.md) (the deferred analysis harnesses).

## Source

Distilled from the working report `notes/publication-path-report.md` (the OneDrive-root analysis, retained outside the published repo for provenance).
