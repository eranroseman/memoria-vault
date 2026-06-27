---
topic: decisions
id: 20
title: Publication path — vault-eval benchmark first, capture-now
nav_exclude: true
status: accepted
date_proposed: 2026-05-27
date_resolved: 2026-06-01
assumes: []
supersedes: []
superseded_by: []
---

# ADR-20: Publication path — vault-eval benchmark first, capture-now

## Context

When this was decided (pre-v0.1 ship), Memoria was a design artifact — rigorous and internally consistent, but it had not yet run a system, produced a benchmark, or surveyed the field. (v0.1 has since shipped and run end-to-end, but it has still produced no benchmark or published contribution, so the strategy below stands.) A 20-paper system survey plus a ~51-paper capability-mapped benchmark review established that no surveyed paper published on design alone; every one ran a system and measured something, shipped a benchmark, or organized the field. The strategic question — which publication shape to aim at, and what to do *first* — was open and blocking: it determines what gets built, what gets instrumented, and in what order. It is live now (not later) because the binding constraint is calendar time on data collection: publications need time series, and the un-backfillable signals (suggestion disposition, operator decision time) are lost forever if capture does not start at first ingest. The full analysis behind this decision — four candidate paths, evidence requirements, and the honest negative space — lives in the source report linked below.

## Decision

Memoria commits to a **two-part publication strategy**:

1. **Target Path 1 first: a vault-eval benchmark paper** (NeurIPS Datasets & Benchmarks track), instantiated via the tractable vault-CiteME within-corpus citation-attribution cell and grounded in the broader "does the vault compound?" framing of [ADR-11 vault-eval](11-vault-eval-maintenance.md). This is chosen over a system paper (Path 2), a position paper (Path 3), or an open-artifact release (Path 4) because it is the only path tractable in months rather than years, has the lowest coupling to a finished system (it needs the Verifier profile and a public fixture, not the whole stack), and forces the measurement layer every downstream path depends on into existence. The system/position papers are explicitly **deferred** until Path 1 has produced data; *which* of them follows is decided by the data, not now.

2. **Start the six-signal instrumented capture now** — the single highest-leverage action, independent of when paper-writing begins. The capture is minimal and adopted in v0.1 (the *analysis* harnesses in [Measurement and verification harnesses](62-measurement-and-verification-harnesses.md) stay deferred): state-transition timestamps, operator decision time, per-card cost, policy deny-reasons, suggestion disposition (accept : edit : reject), and FAMA exposure. Schemas are pinned in [Telemetry & logs](../reference/telemetry.md). Capture precedes analysis because capture cannot be back-filled.

## Consequences

- **Build order is now ordered by the paper, not by feature appeal.** The Verifier profile and a public vault-CiteME fixture are the critical path; everything else is downstream. The board-export cron (Phase 1 in the [timeline](https://github.com/eranroseman/memoria-vault/blob/main/docs/releasing/0.1.0-alpha.1/release-plan-0.1.0-alpha.1-appendix.md)) becomes a publication prerequisite, not just an observability nicety — without it the board-state and cost logs never populate. The former cost/disposition gap is closed by [ADR-106](106-cost-and-disposition-capture.md): cost joins completed cards to the Hermes session store, and suggestion disposition is captured at the review action.
- **The de-risking is deliberate.** If within-vault citation-attribution numbers come out *worse* than public CiteME, the Verifier-as-gate thesis weakens — and we learn that before staking a system paper on it.
- **n=1 operator data is accepted as a known weakness** of the later system-paper path, to be mitigated by detailed logging and a within-subject comparison arm (blocking vs. advisory review, see [ADR-41](41-configurable-review-gate-mode.md)) rather than by more operators.
- **The novelty surface is fixed to a triad** — policy-MCP-enforced zone permissions, structurally blocking review state, and structural human-set claim supersession ([ADR-10](10-claim-supersession.md)) as the answer to the FAMA failure mode — plus the measurable knowledge-work consequences that only data can supply. We explicitly will **not** anchor a paper on the seven-profile design, the LLM-Wiki/Zettelkasten/Memex synthesis, or Obsidian-as-substrate; each is prior art or operational, not contributory.
- A higher-novelty framing (Path 1′, vault-eval as the contribution rather than vault-CiteME as an instance) remains available and costs more fixture work; the choice between the two framings is left to paper-drafting time and does not change this decision.

## Alternatives considered

**Lead with a system paper (Path 2).** Rejected as the *first* move: 6–9 months, requires the full MVS + Librarian + Verifier + Linter stack and a comparison study, and needs a defensible "operator hours saved per unit of vault growth" metric that does not yet exist in the field. It is the natural *second* paper once Path 1 has produced data.

**Lead with a position paper (Path 3).** Rejected as first: position papers without empirical work get rejected, and with strong empirical work they compete with full system papers — a narrow sweet spot. Its field-survey prerequisite is largely satisfied by the ~51-paper taxonomy, but it still needs the same empirical evidence as Path 2.

**Open-artifact release (Path 4).** Rejected as first: longest horizon — needs a real implementation, adopter-facing docs, and external adoption stories that take time to accumulate.

**Defer instrumentation until the system is "finished."** Rejected outright: disposition and decision-time signals cannot be reconstructed after the fact, so waiting discards the most valuable data permanently. Capture is decoupled from paper-writing and starts at first ingest.

## Related

- **Files affected:** [Telemetry & logs](../reference/telemetry.md) (the six-signal schemas), [Release plan — v0.1.0-alpha.1 — appendix](https://github.com/eranroseman/memoria-vault/blob/main/docs/releasing/0.1.0-alpha.1/release-plan-0.1.0-alpha.1-appendix.md) (step 8, six-signal capture; board-export cron is the prerequisite).
- **Related decisions / Depends on:** [ADR-11 vault-eval](11-vault-eval-maintenance.md) (the eval program this paper instantiates); [ADR-10 claim supersession](10-claim-supersession.md) (the FAMA-exposure signal and a novelty-triad pillar); [ADR-03 structural review gate](03-structural-review-gate.md) (the blocking-review thesis the later system/position paper would test).
- **Proposals:** [Measurement and verification harnesses](62-measurement-and-verification-harnesses.md) (analysis harnesses, deferred); [ADR-41](41-configurable-review-gate-mode.md) (the comparison arm); [ADR-106](106-cost-and-disposition-capture.md) (the cost/disposition capture path).
- **Supporting rationale:** [Why Memoria doesn't pursue full autonomy](../design/why-not-autonomous.md), [Pattern provenance: borrow, adapt, ignore](../design/why-pattern-provenance.md), [Why the review gate is structural](../design/why-human-gate.md), [Intellectual foundations](../design/intellectual-foundations.md).
- **Source discussion:** originally distilled from the working report `notes/publication-path-report.md` (retained outside the repo for provenance).
