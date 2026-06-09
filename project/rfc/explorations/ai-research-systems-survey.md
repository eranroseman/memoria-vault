---
topic: proposals
title: AI-research systems survey — the evidence behind the provenance table
status: stub
created: 2026-06-09
---

# AI-research systems survey — the evidence behind the provenance table

> **STUB — research not yet done.** This is a placeholder for the working survey that
> produced the Borrow / Adapt / Reference / Ignore judgment table in
> [`docs/explanation/rationale/why-pattern-provenance.md`](../../../docs/explanation/rationale/why-pattern-provenance.md).
> The polished *conclusion* lives in that explanation page; the *evidence* — per-system
> notes, the quantitative finding behind each verdict, the citations — was never
> recorded here. Until filled in, the provenance table is assertion-rich and
> uncheckable.
>
> **How to fill this in:** this is **not** a from-scratch re-survey of all ~47 systems.
> It is an **evidence appendix**: for each pattern in the provenance table, record the
> primary citation and the one quantitative result that justifies its verdict, then
> adversarially verify that result against its source. Use the
> [`deep-research`](../../../) harness per claim.

## Why this is needed

The pattern-provenance page classifies each surveyed pattern as **Borrow** (adopt as-is),
**Adapt** (take the mechanic, strip the autonomy), **Reference** (informs positioning),
or **Ignore** (evaluated and refused). Many entries cite a specific empirical figure as
the reason for the verdict. Those figures currently trace to nothing verifiable in the
repo. This appendix is what makes the table auditable: a reader should be able to follow
any verdict to a checked source.

## Sample claims to verify (quoted from the provenance page; ⚠️ unverified)

| Verdict | Pattern / finding (as cited) | Source | Status |
|---|---|---|---|
| Borrow | File-as-Bus ablation: removing the artifact bus drops PaperBench 6.41 / MLE-Bench Lite 31.82 | Chen et al. 2026 | ⚠️ unverified — also in [memory-systems-and-benchmarks.md](memory-systems-and-benchmarks.md) |
| Borrow | Claim-to-evidence by construction: **0/337 hallucinated references** vs. baselines up to 21% | ScientistOne (Meng et al. 2026) | ⚠️ unverified |
| Adapt | Citation-attribution: frontier LMs hit **4–18%**, CiteAgent reaches **35%** | CiteME (Press et al. 2024) | ⚠️ unverified |
| Adapt | Agent-readable shared synthesis pool: **~11%** gain on MATH-500 | AgentRxiv (Schmidgall & Moor 2025) | ⚠️ unverified |
| Adapt | Per-paper structured representation: **+29–42 pp** over raw PDF | Knows (Yu & Wang 2026) | ⚠️ unverified |
| Reference | Artifact-aware review exposes fabrication manuscript-only review misses (117-paper audit) | Zhang et al. 2026 | ⚠️ unverified |
| Ignore | Co-trained reviewer: **26.89% MAE** on paper scoring → metric becomes learned, not fixed | CycleResearcher (Weng et al. 2025) | ⚠️ unverified |

*(The full table in the provenance page has ~50 entries across the four verdicts; the
rows above are a representative sample of the ones carrying a checkable figure.)*

## Structure to fill in

1. **Method & scope** — what "~47 systems, May 2026" actually covered; inclusion
   criteria; how the four verdicts were assigned.
2. **Evidence per verdict class** — Borrow / Adapt / Reference / Ignore, each row with
   citation + verified figure, mirroring the provenance table 1:1.
3. **The intellectual foundations** — Memex / Zettelkasten / Karpathy / Matuschak as
   the non-agent lineage (low re-research priority; the polished page is stable).
4. **Discrepancy log** — any figure that did **not** survive verification, with the
   corrected value and the ADR/doc that needs updating.

## Related

- [`docs/explanation/rationale/why-pattern-provenance.md`](../../../docs/explanation/rationale/why-pattern-provenance.md) — the table this appendix backs
- [`docs/explanation/overview/intellectual-foundations.md`](../../../docs/explanation/overview/intellectual-foundations.md) — the foundations lineage
- [memory-systems-and-benchmarks.md](memory-systems-and-benchmarks.md) — sibling stub; the durable-state rows overlap
- Reference: [`docs/reference/bibliography.md`](../../../docs/reference/bibliography.md)
- Touches verdicts realized in [measurement-and-verification.md](measurement-and-verification.md), [classical-method-displacements.md](classical-method-displacements.md), and [schema-and-retrieval.md](schema-and-retrieval.md)
