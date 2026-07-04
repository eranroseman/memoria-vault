---
topic: decisions
id: 128
title: No write-time correctness oracle — checked ≠ approved
nav_exclude: true
status: accepted
date_proposed: 2026-07-02
date_resolved: 2026-07-02
assumes: [127]
supersedes: [3, 21, 41, 54, 57]
superseded_by: []
---

# ADR-128: No write-time correctness oracle — checked ≠ approved

Consolidation ADR (see ADR-125 preamble). This is the deliberate reversal of
the corpus's founding epistemics. It supersedes ADR-03 (human approval as the
only path to canonical), ADR-21 ("cheaper reviews, never fewer" — confidence
routing foreclosed), ADR-54 ("no confidence-tiered auto-accept anywhere"),
ADR-41 (gate modes), and the disposal half of ADR-57. The evidence is inlined
because the source corpus (`_papers/`) is gitignored.

## Context

ADR-03/21/54 assumed two things: that knowledge-work errors are effectively
irreversible (so creation must be gated), and that a human reviewing each
machine write improves correctness. The adversarial literature pass refuted
the second and ADR-127 removed the first:

- **Human + machine ≯ machine.** Jacobs 2021 (N=220, within-subject):
  clinician+ML accuracy 0.356 ≈ clinician-alone 0.357, both far below ML-alone
  0.667; an incorrect recommendation dragged the human *below* their own
  no-recommendation baseline (0.299 vs 0.357, p=0.0018). The reviewer did not
  filter the error; the error contaminated the reviewer. Explanations made it
  worse (incorrect rec + explanation was the lowest-accuracy condition, 0.262,
  p=0.004); confidence displays were uncalibrated.
- **Dense per-item approval erases automation and trains rubber-stamping.**
  AutoResearchClaw's HITL ablation: targeted intervention at 3–6 checkpoints
  dominates per-step approval; time-constrained experts refuse to re-decide
  trust at every point. Verification asymmetry (Feng & Liu): auditing an
  artifact needs the builder's expertise, so under load the gate degrades to a
  cursory nod — at exactly single-researcher scale.
- **Reversibility is restored.** ADR-127's quarantine-and-verify, consumption
  guard, demotion propagation, and cascade rollback make any error detectable,
  attributable, and cheaply undoable, with the blast radius a graph query.
  The precondition that justified gating creation no longer holds.

## Decision

- **Correctness is not conferred at write time by any approver, human or
  machine.** A human-authored note and an LLM digest are epistemically equal:
  fallible claims entering the same envelope, the same checks, the same
  journal, the same rollback graph. Provenance records who authored; *who*
  confers no trust.
- **`checked` means "checks passed and warrants resolve" — never "approved."**
  No surface, schema, doc, or help text may describe `checked` as
  approved/verified/trusted (enforced by an `rg` gate). Promotion is only by
  the shared check suite; demotion is fail-closed and propagating (ADR-127).
- **The human checkpoint is calibrated or thinned.** Humans are routed to
  act/ask/log findings consequence-first, only where checkpointed items are
  measurably more correct than the same items un-checkpointed. A checkpoint
  that cannot beat its no-checkpoint baseline is theatre and is thinned.
  This deliberately re-admits the consequence/uncertainty routing that ADR-21
  foreclosed — with the theatre-check as the new guard in place of the
  blanket rule.
- **Dispositions are first-class, non-backfillable telemetry.** Every
  `attention resolve` journals the routing class (act/ask/log) and the human
  resolution outcome (apply/reject/defer) with decision time, from the first
  ingest. This is what makes "calibrated" falsifiable, and the apply-rate
  bounds are the rubber-stamp detector (persistently >0.9 or <0.2 flags).
- **From ADR-57, the writer half survives; the disposal half does not.** Any
  rule-derivable write is engine code, never an LLM ("engines write" — and
  57's evidence stands: pinned models bound drift, they do not buy
  reproducibility). But "agents judge, PI approves" is replaced by "checks
  route, propagation protects, calibrated humans decide where they measurably
  help." No machine verdict is a gate by itself (ADR-129).
- **From ADR-41, the review gate names the write mechanism, not board motion.**
  The one structural stop that remains is at the write itself:
  `src/memoria_vault/runtime/policy/decision.py` enforces that the
  hard stop is at the write, never at kanban card advancement.

## Consequences

- The review queue as an approval surface is gone; the attention surface is a
  consequence-routed worklist that must keep the honesty-card obligations
  (arguments, not verdicts; batch worklists; graded loudness).
- Safety claims move from "a human saw it" to invariants with gates:
  quarantine, propagation, rollback, and the calibration fixture.
- If disposition telemetry shows a checkpoint underperforming its
  no-checkpoint baseline, thinning it is mandatory, not optional.

## Alternatives considered

- **Keep the structural per-write gate (ADR-03)** — rejected on the evidence
  above: it charged the scarcest resource (PI attention) for correctness it
  measurably did not buy, and its throughput ceiling throttled the whole loop.
- **Confidence-routing without the theatre-check** — rejected: that is the
  failure ADR-21 rightly feared; the calibration fixture is the load-bearing
  difference.
- **LLM reviewer as the gate** — rejected, unchanged: a probabilistic verdict
  is never a structural control (ADR-129 keeps every LLM judge a proposer).

## Related

- ADR-127 (the machinery), ADR-129 (machine judgment stays proposer-only).
