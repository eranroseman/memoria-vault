---
title: Publication path — what would make Memoria worth publishing
date: 2026-05-27
updated: 2026-05-29
status: decided (distilled into ADR-24)
scope: assessment of viable publication paths grounded in the 20-paper system survey (papers/) and the ~51-paper benchmark review (benchmarks/)
sibling: papers-vs-memoria-report.md
decision: ../memoria-vault/project/decisions/24-publication-path.md
proposal: ../memoria-vault/project/proposals/publication-strategy.md
---

# Publication path — what would make Memoria worth publishing
>
> **Decided 2026-06-01.** The recommendation in this report — pursue Path 1 (vault-eval / vault-CiteME) first and start the six-signal capture now — is adopted as [ADR-24](../memoria-vault/project/decisions/24-publication-path.md). The full four-path analysis is now versioned in the repo as the proposal [publication-strategy.md](../memoria-vault/project/proposals/publication-strategy.md) (with canonical links and the deferred Path 2/3 choice). This document is the original working analysis, retained outside the repo for provenance; the ADR is the authoritative decision and the proposal is the authoritative analysis.

## Executive summary

Memoria is currently a design artifact — rigorous, well-rationalized, internally consistent. None of the 20 surveyed papers got published on design alone; every one of them either ran a system and measured something, introduced a benchmark, or surveyed the field. Memoria does none of those three yet.

**The single biggest gap between current Memoria and any publication path is a running system that has produced data.** Every viable path routes through this — even the position-paper option, which appears at first glance not to need empirical work, actually needs the most.

This report identifies four publication shapes Memoria could fit, characterizes the work each requires, and recommends a sequence. The recommendation is to pursue the vault-CiteME benchmark paper first (Path 1), because it is the only path tractable in months rather than years and because every downstream path needs the measurement infrastructure it forces into existence.

The recommendation also names the single highest-leverage action available today: **start running the MVS with instrumented timing logs.** Publications need time series, not snapshots; three months of operator data is more valuable than three months of further design work.

## Update — 2026-05-29 (benchmark review)

Since this report was drafted, the informal 20-paper survey was expanded into a ~51-paper, capability-mapped benchmark review (`benchmarks/`; synthesis in [evaluation.md](../developer-guide/roadmap/evaluation.md)). Three things shift the picture below — none reverse the recommendation; all sharpen it:

1. **The measurement infrastructure this report treats as hypothetical is now designed.** [vault-eval](../developer-guide/decisions/23-vault-eval-integration.md) (a system-level gold-set eval, Linter-scored, non-gating) and a [CiteME-style Verifier regression harness](../developer-guide/roadmap/future-directions.md#citeme-style-verifier-regression-harness) are specified, along with *borrowed* metrics the field already validates — **FAMA** (penalizes obsolete-memory reuse), **pass^k** (reliability across repeated runs), **coverage@k**, **CRS**. Path 1 no longer has to invent the measurement layer; it has to *run* it. This strengthens the "run the MVS now" action in §5.

2. **Path 3's "formal field survey" prerequisite is largely satisfied.** The [capability-mapped taxonomy](../developer-guide/roadmap/evaluation-benchmarks.md) — ~51 benchmarks tagged by capability and adoption mode (run / borrow / validate), with explicit out-of-scope categories — *is* the field survey Path 3 said it still needed. The position-paper skeleton is closer than this report assumed.

3. **The novelty claim gains externally-grounded material.** The long-term-memory benchmark cluster (LongMemEval, Memora/FAMA, MemoryAgentBench, ClawArena) is *citation-disconnected* from the scientific-research-agent literature — a measurement gap that is itself a publishable observation. And the review warranted exactly **one** structural design change ([claim supersession / ADR-22](../developer-guide/decisions/22-claim-supersession.md)) plus two refinements, *validating* the rest of the design — external corroboration that directly arms a position paper. See §6.

The original analysis below stands; these notes layer the new evidence onto it.

## 1. Publication shapes in the surveyed field

The 20 papers in the system/method survey (`papers/`) cluster into 5 publication shapes — a different corpus from the ~51-paper capability-benchmark review (`benchmarks/`) in the Update above:

| Shape | Surveyed examples | Count |
| --- | --- | --- |
| System paper (working system + capability evaluation) | AI Scientist, AI-Researcher, Agent Laboratory, AI co-scientist, AgentRxiv, CORAL, AiScientist (Chen 2026), MLR-Copilot, MetaGPT, OpenHands, AutoGen, ResearchAgent | 12 |
| Benchmark paper (public benchmark + frontier-model evaluation) | LitSearch, CiteME, ResearchArena | 3 |
| Method paper (specific technical advance with measurement) | SciMON, MOOSE (Yang 2024), Qi 2023 | 3 |
| Survey (organize the field, name the patterns) | Gridach 2025 | 1 |
| Domain-adapted model paper | SciLitLLM | 1 |

Each shape has different evidence requirements. Picking a shape determines what work needs doing. Memoria's design is shape-agnostic today; choosing a shape is the unblocking move.

## 2. Where Memoria currently stands vs. each shape

| Shape | What it needs | What Memoria has | What's missing |
| --- | --- | --- | --- |
| System paper | Working impl + capability evaluation vs. baseline | Design only | Implementation, baseline comparison, metric |
| Benchmark paper | Public benchmark + frontier-model evaluation + dataset | A *designed harness* — [vault-eval](../developer-guide/decisions/23-vault-eval-integration.md) + a [CiteME-style fixture](../developer-guide/roadmap/future-directions.md#citeme-style-verifier-regression-harness) | Public artifact, frontier evals, release |
| Method paper | A specific technical advance with measurement | None claimed today | A measurable novel technique |
| Position / argument paper | A strong claim + supporting evidence + clear contrast | Strong design rationale | Empirical evidence, comparison data |
| Tools / artifact paper | Mature open-source repo + adoption | None public | All of it |

The design rationale that already exists is worth 30–50% of any of these shapes — none of them ships without it. But none of them ships *with only* design either.

## 3. Four viable paths, ordered by tractability

### Path 1 (most tractable) — vault-CiteME benchmark paper

**Claim.** "We introduce vault-CiteME, a within-corpus citation-attribution benchmark for AI research assistants, and evaluate N frontier models against the Memoria Verifier profile."

**Venue.** NeurIPS Datasets & Benchmarks Track. Workshop tracks at ICLR / EMNLP for an earlier version.

**Why this is the lowest bar.** CiteME (Press 2024) was already accepted at NeurIPS Datasets & Benchmarks; there is a clear comparable. The contribution is the *within-vault* variant — bounded candidate space, different failure mode, different operator stakes than public-corpus attribution. Frontier LMs get 4–18% on public CiteME (tooled CiteAgent ~35%); the within-vault number is unknown, and *that gap is the paper's empirical core*. The benchmark review sharpens the comparables — **CiteGuard** (retrieval-aware attribution; extends CiteME) and **Wallat 2024** (correctness ≠ faithfulness: a *similar* note is not a *supporting* one) — and reframes vault-CiteME as the citation-attribution slice of the broader [vault-eval](../developer-guide/decisions/23-vault-eval-integration.md) program (*does the vault compound?*), which is arguably the more novel benchmark contribution.

**Work required.** ~3–4 months part-time:

1. Build a public 200-example vault-CiteME fixture (synthetic vaults or anonymized real-vault excerpts).
2. Evaluate 3–5 frontier models + 2 retrieval baselines.
3. Compare to public CiteME numbers to characterize the within-vault setting.
4. Release fixture + evaluation code + Memoria Verifier profile.

**What this paper would *not* claim.** That Memoria is the right design. That blocking review beats advisory review. That single-user is the right scope. All those claims are deferred to later papers.

### Path 1′ (higher-novelty framing of Path 1) — vault-eval as the contribution

**Claim.** "We introduce *vault-eval*, a methodology and metric suite for measuring whether a curated, human-gated knowledge vault *compounds* — does the system find, verify, answer, and remember better *on its own growing corpus* over time? — instantiated on the Memoria vault across N workflows."

**Venue.** Same (NeurIPS Datasets & Benchmarks). The framing, not the venue, differs.

**Why it's more novel than Path 1.** vault-CiteME is a CiteME variant — incremental by construction. vault-eval asks a question no benchmark in the ~51-paper review answers: not "how good is the model on a foreign corpus?" but "does *this* vault pay off as it grows?" It is a *system-level, corpus-native* eval, and it adapts metrics the field already validates into a PKM setting — **FAMA** (obsolete-memory reuse → claim staleness), **coverage@k** (loose ends), **pass^k** (lane reliability), **CRS** (completion × robustness), plus human-loop **disposition** (accept : edit : reject). The methodology + metric-adaptation *is* the contribution.

**The honest catch — harder to publish than Path 1.** A benchmark paper needs a *public artifact* and a *clean comparable*; vault-eval has neither natively. Its gold set is, by design, *your* vault (private, single-user), and there is no prior "does-the-vault-compound" number to beat. To publish it you must manufacture both: a *released synthetic / anonymized gold vault* others can run, and a defensible baseline (e.g., the same metrics on an untyped or advisory-review variant). That is strictly more work than vault-CiteME, which inherits CiteME's public-fixture pattern and comparator.

**The resolution — they are not competing paths.** vault-CiteME is the *tractable instance* that grounds the methodology; vault-eval is the *frame*. The strongest single paper is **"vault-eval, instantiated via two cells"** — citation attribution (vault-CiteME) and claim staleness (FAMA exposure) — shipped with a released synthetic gold vault. That earns the framing's novelty while keeping one foot on Path 1's tractable ground. Choose **Path 1** if the priority is *landing a paper fast*; choose **Path 1′** if the priority is *the more cited, more defensible contribution* and you can absorb the extra fixture-construction work.

### Path 2 — System paper anchored on a specific capability

**Claim.** "Memoria: A vault-centered research operating system with structurally blocking human review. We demonstrate X% reduction in [specific operator pain point] compared to [baseline]."

**Venue.** CHI, CSCW, or UIST — HCI venues that take design-plus-evaluation. ACM Queue for a practitioner-facing version.

**The hard problem.** Picking the right metric. Memoria's design pitch is "bookkeeping, not intelligence" — the right comparison is *operator hours saved per unit of vault growth*, not *task accuracy*. That metric does not exist in the field; you would have to define it and defend it.

**Work required.** ~6–9 months:

1. Implement MVS + Librarian + Verifier + Linter profiles (the minimum stack that demonstrates the blocking-review thesis).
2. Run 3 months of personal use with instrumented logging (every card, every state transition, every operator decision time).
3. Run a 4–6 week comparison study — same vault, two operators, one using Memoria's blocking review and one using an advisory-review variant (or a generic-LLM-assistant baseline like ChatGPT-with-files).
4. Quantify operator time-per-claim, false-promotion rate, vault link density, and trust metrics over time.

**Risk.** n=1 or n=2 operator studies are publishable at CHI but draw skepticism. Mitigated by detailed logging and qualitative methodology.

### Path 3 — Position paper + small empirical study

**Claim.** "Contemporary autonomous-research systems optimize for the wrong objective shape (scalar metrics, autonomous keep/revert, advisory review). We argue that for knowledge work, structural human-blocking review is the correct architectural commitment, and show [small empirical study] supporting the position."

**Venue.** TOCHI, ACM Queue, arXiv + a workshop. Possibly Communications of the ACM if the rhetoric is strong.

**Why this is harder than it looks.** Position papers without empirical work get rejected; position papers with strong empirical work compete with full system papers. The sweet spot is narrow.

**Strengths Memoria already has.** The 7-row scalar-metric table in [why-no-autonomous-synthesis.md](../developer-guide/architecture/why-no-autonomous-synthesis.md). The borrow / adapt / ignore table in [why-pattern-provenance.md](../developer-guide/architecture/why-pattern-provenance.md). The advisory-vs-blocking review observation in [vision.md](../developer-guide/vision.md). The Chen 2026 + AgentRxiv empirical citations in [architecture/README.md](../developer-guide/architecture/README.md). **New:** the benchmark review independently *validates* the core posture (deterministic ingest, blocking gate, narrow per-lane profiles, vault-as-distilled-memory) — the external corroboration a "this design is correct" claim needs. These are the skeleton of a real position argument.

**Work required.** ~9–12 months:

1. Everything in Path 2 (you need empirical evidence).
2. A formal field survey — **largely satisfied**: the [~51-paper capability-mapped taxonomy](../developer-guide/roadmap/evaluation-benchmarks.md) (run / borrow / validate adoption modes, explicit out-of-scope categories) is the field survey, and it surfaces a distinctive finding — the long-term-memory benchmark cluster is citation-disconnected from the research-agent literature.
3. A "shape" comparison between Memoria and 3 reference systems (e.g., AI Scientist, Agent Laboratory, AI co-scientist) on common tasks where applicable.

### Path 4 (longest horizon) — Memoria as an open artifact

**Claim.** "We release Memoria, a vault-centered research OS, with documented evidence of N months of use across M researchers."

**Venue.** SoftwareX, JOSS (Journal of Open Source Software), arXiv tools papers, or an HCI venue with a tools track.

**Why this is longest.** Requires a real implementation, documentation aimed at adopters, at least one external adopter, and time for adoption stories to accumulate.

**Strengths.** Memoria's integration with widely-used tools (Obsidian, Zotero, Hermes) is a real adoption asset. Most surveyed systems are research code; Memoria could be the *operationally usable* alternative.

## 4. Recommendation

**Pursue Path 1 first** — under either framing: the tractable vault-CiteME (Path 1) or the higher-novelty vault-eval (Path 1′); see §3. Reasons, in order of importance:

1. **Tractable.** 3–4 months part-time vs. 6–12+ for other paths.
2. **Low coupling.** Does not require Memoria to be fully built — only the Verifier profile and the public fixture.
3. **Establishes credentials.** A published benchmark paper makes the subsequent system / position paper much easier to land — reviewers stop questioning whether the authors know the field.
4. **Instantiates the measurement infrastructure (now designed).** The eval layer is no longer hypothetical — [vault-eval](../developer-guide/decisions/23-vault-eval-integration.md), the CiteME-style fixture, and borrowed metrics (FAMA, pass^k, coverage@k) are specified. Path 1 *runs* this layer rather than inventing it; every downstream path needs it.
5. **De-risks the bigger claim.** If the within-vault numbers turn out *worse* than public CiteME (a surprise), Memoria's Verifier-as-gate thesis weakens and you learn that before staking a system paper on it.

After Path 1 lands, the choice between Path 2 (system paper) and Path 3 (position paper) depends on the data accumulated by then. The data, not the choice, is the binding constraint.

## 5. The single highest-leverage action this month

**Start running the MVS instrumented with timing logs.**

Every other path needs operator data. The earliest possible measurement is the most valuable measurement, because publications need *time series*, not snapshots — "Memoria over 6 months" is publishable; "Memoria last Tuesday" is not. Three months from now you either have a baseline you can compare against, or you don't.

The instrumentation requirement is small:

- Per-card timestamps for every state transition (already in the board schema).
- Operator decision time per `awaiting-review` card.
- Cost per task (API spend per card).
- Failure modes (deny reasons from the policy MCP).
- Suggestion disposition — the accept : edit : reject ratio per profile (the clearest human-loop signal; cannot be backfilled).
- FAMA exposure — drafts/answers citing a superseded claim (the [supersession](../developer-guide/decisions/22-claim-supersession.md) mechanism makes this measurable).

This is operational logging Memoria already specifies (now detailed in [success-metrics.md](../developer-guide/roadmap/success-metrics.md) and [evaluation.md §Observability](../developer-guide/roadmap/evaluation.md)). What's missing is the discipline of *running it now*, before the system is "finished," so that the time series starts accumulating.

Everything else in this report is downstream of having that data.

## 6. What Memoria probably *cannot* publish on, honestly

The negative space matters too. Three superficially-attractive claims that would not survive review:

- **The seven-profile design alone.** MetaGPT, AI co-scientist, and Agent Laboratory already published multi-role architectures. Memoria's profile design is internally consistent but not novel enough to anchor a paper.
- **The Karpathy LLM-Wiki + Zettelkasten + Memex synthesis.** Beautifully argued in [vision.md](../developer-guide/vision.md), but the three components are well-known. The novelty has to be in what Memoria *does* with them, not in the synthesis.
- **Obsidian-as-substrate.** Many systems use Obsidian; this is operational, not contributory.

The novelty Memoria *can* claim is the triad:

1. **Policy-MCP-enforced zone permissions** (per-folder write degradation, not per-agent prompt discipline).
2. **Structurally blocking review state** (`awaiting-review → approved` as a state machine, not as an annotation).
3. **Structural, human-set claim supersession** as the dependable answer to the FAMA failure mode (reusing obsolete memory) that the memory-benchmark cluster — Memora/FAMA, ClawArena — shows is the *least reliably automatable* memory capability. Carrying it by bookkeeping rather than inference ([ADR-22](../developer-guide/decisions/22-claim-supersession.md)) is a genuine, externally-motivated contribution.
4. **Measurable consequences for knowledge-work outcomes** (the part that requires the data).

The first three are present in the design today (supersession was added by the benchmark review). The fourth is what every publication path routes through.

## 7. Sequence summary

| Horizon | Action | Output |
| --- | --- | --- |
| This month | Start instrumented MVS use | Baseline time-series begins |
| Months 1–4 | Path 1: vault-CiteME benchmark | Workshop or NeurIPS D&B submission |
| Months 4–9 | Continue instrumented use; build Verifier + Librarian fully | 6 months of operator data |
| Months 9–15 | Path 2 or Path 3 (whichever the data supports better) | CHI / CSCW / TOCHI submission |
| Beyond | Path 4: open-artifact release | JOSS / SoftwareX submission, external adoption |

The schedule is aggressive but not unrealistic for part-time work. The binding constraint is whether the instrumented use starts now or in six months. Six-month delay pushes everything else proportionally.

— end —
