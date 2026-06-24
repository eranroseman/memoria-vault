---
title: What the literature pushes back on
parent: Design rationale
nav_order: 8
---

# What the literature pushes back on

[Pattern provenance](why-pattern-provenance.md) records where the corpus *supports* Memoria. This page records where it pushes back. It is drawn from the project's own adversarial review pass (`REVIEW-REFUTATIONS.md`), which inverted the confirm-only method and found that the corpus endorses Memoria's **skeleton** — durable state, nightly batch surfacing, the review gate, verbatim warrants, tabular projection — while contradicting several of the **stronger claims** layered on top. None of the surveyed bets survived adversarial scrutiny untouched; the honest reading is "validated skeleton, contested superstructure."

The claims to scope back:

- **Least-privilege allowlists are *necessary blast-radius control, not sufficient security*.** Removing send/exec tools genuinely breaks the exfiltration step, but the dominant threat to Memoria is untrusted *data* — a poisoned ingested paper whose legitimate read-and-reason path *is* the attack — which no allowlist stops. The gate plus provenance and channel separation are the integrity controls, and none is foolproof.
- **The human gate buys provenance and control, not guaranteed accuracy.** In the one corpus study that measured it, human-plus-machine accuracy did not beat human-alone, and a confidently wrong recommendation dragged the reviewer *below* their own baseline. Treat "the PI approves" as control and auditability, and calibrate whether approved writes are actually more correct — or the gate is theater.
- **The gate should be sparse and uncertainty-routed, not item-by-item.** Dense per-step approval erases the automation it guards; route to the PI only on high-uncertainty or high-leverage items, and accept that low-stakes writes are not meaningfully human-verified.
- **Superseded claims stay retrievable.** Hard-excluding a superseded claim breaks the cross-period and trend queries that need the historical baseline. Don't present a stale claim *as current*; keep it tagged and reachable.
- **Atomic claims need explicit context fields.** A claim ripped from its source loses temporal scope, tense, and hedging. Carry those as first-class fields, and treat the atomic claim as an *index over* the verbatim contextual unit rather than the stored unit itself.
- **Contradiction and dedup must pass an adversarial overlap test.** Entailment models inherit the same "shared words ⇒ same meaning" blind spot as cosine; require a high-overlap/opposite-meaning fixture as an acceptance gate before any comparator is allowed to gate dedup or supersession.
- **Constrained decoding buys structural validity only.** A schema can force a well-formed list; it cannot force the model to *omit* an absent claim or preserve negation. Keep existence-gating and explicit abstain paths as engine stages, and validate content even on schema-valid output.

These are scoping corrections, not refutations of the design. The skeleton holds; the superstructure should claim less.

---

## Related

- Where the corpus *supports* these bets: [Pattern provenance: borrow, adapt, ignore](why-pattern-provenance.md)
- The gate this scopes: [Why the review gate is structural](why-human-gate.md)
- The sandbox this scopes: [Why the architecture is layered](why-three-layers.md)
