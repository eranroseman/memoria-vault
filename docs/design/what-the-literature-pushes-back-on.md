---
title: What the literature pushes back on
parent: Design
nav_order: 31
---

# What the literature pushes back on

[Pattern provenance](why-pattern-provenance.md) records where the corpus *supports* Memoria. This page records where it pushes back. It is drawn from the project's own adversarial review pass (`REVIEW-REFUTATIONS.md`), which inverted the confirm-only method and found that the corpus endorses Memoria's **skeleton** — durable state, nightly batch surfacing, the review gate, verbatim warrants, tabular projection — while contradicting several of the **stronger claims** layered on top. None of the surveyed bets survived adversarial scrutiny untouched; the honest reading is "validated skeleton, contested superstructure."

The claims to scope back:

| Claim | Pushback | Design consequence |
| --- | --- | --- |
| Least-privilege allowlists are sufficient security | Poisoned input can attack through a legitimate read-and-reason path. | Keep allowlists, but rely on gate, provenance, and channel separation for integrity. |
| Human approval guarantees accuracy | Human-plus-machine can underperform human-alone when the machine is confidently wrong. | Treat approval as control and auditability; measure whether it improves correctness. |
| More approval is always safer | Dense item-by-item approval erases automation and trains rubber-stamping. | Route only high-uncertainty or high-leverage items. |
| Superseded claims can disappear | Historical queries need the old baseline. | Mark them non-current, but keep them retrievable. |
| Atomic claims are self-sufficient | Stripped claims lose temporal scope, tense, and hedging. | Carry context fields and source-span provenance. |
| Similar wording means same meaning | Entailment models can still confuse high-overlap opposites. | Require adversarial overlap fixtures before dedup or supersession gates. |
| Schema-valid output is content-valid | Constrained decoding preserves shape, not truth or negation. | Keep existence checks, abstain paths, and content validation. |

These are scoping corrections, not refutations of the design. The skeleton holds; the superstructure should claim less.

---

## Related

- Where the corpus *supports* these bets: [Pattern provenance: borrow, adapt, ignore](why-pattern-provenance.md)
- The gate this scopes: [Why the review gate is structural](why-review-gate-is-structural.md)
- The sandbox this scopes: [Why the architecture is layered](why-layered-architecture.md)
