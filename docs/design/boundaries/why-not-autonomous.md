---
title: Why Memoria doesn't pursue full autonomy
parent: Boundaries
grand_parent: Design
nav_order: 4
---

# Why Memoria doesn't pursue full autonomy

Memoria targets L3 on the autonomy spectrum — multi-step autonomous execution under human-set strategy with per-batch review — and maintains a structurally enforced ceiling. This document explains why the ceiling exists and where the exception lies.

---

## The three preconditions for autonomous loops

[Karpathy](../../reference/bibliography.md#karpathy-llm-wiki)'s Autoresearch pattern — an agent that runs overnight, modifies code, tests against a fixed evaluator, and keeps or reverts — works because three conditions hold simultaneously:

1. **The metric is monotonic.** Validation loss either improves or it doesn't.
2. **Changes are reversible.** Git reverts the diff; the next experiment starts clean.
3. **Experiments are independent.** Experiment N+1 doesn't depend on the conclusions of N.

An autonomous keep/revert loop is only safe when all three conditions hold. The loop optimizes a scalar; the scalar must be the right signal; errors must be correctable without downstream consequences.

---

## Why knowledge work fails the test

**Synthesis quality is not scalar.** Every autonomous research system (AI Scientist, [AI co-scientist](../../reference/bibliography.md#gottweis2025aicoscientist), CORAL, [SciMON](../../reference/bibliography.md#wang2024scimon), Karpathy Autoresearch, [Chen et al. 2026](../../reference/bibliography.md#chen2026autonomous)) uses one number as the keep/revert signal. That number is plausible for its target task. None of these numbers is plausible for "is this synthesis a faithful, well-cited, non-redundant addition to a research vault." The proxy metrics that exist — citation count, relevance score, Scite support count — can inform triage priority, but they don't measure synthesis correctness.

**Synthesis errors compound.** In ML benchmarking, a wrong experiment is a wasted run. In knowledge work, a wrong claim persists in the vault and gets cited by downstream notes that build on it. The cost model is inverted: errors don't stay local; they accumulate. This asymmetry means the tolerance for autonomous keep/revert is much lower for knowledge work than for code experiments.

**Later sources reinterpret earlier ones.** Experiments in ML are independent. In knowledge work, they are not — a paper published six months later may show that an earlier claim was wrong, or provide the framework needed to understand what an earlier paper was actually arguing. The value of a source is often only knowable in retrospect.

---

## Why confidence-routing doesn't help

Confidence routing, such as SmartPause in AutoResearchClaw ([Liu et al. 2026](../../reference/bibliography.md#liu2026autoresearchclaw)), routes to the human only when self-assessed confidence is low. Memoria refuses it for two reasons:

| Reason | Why it matters |
| --- | --- |
| Confident-wrong is the failure mode | Hallucinated citations and fabricated numbers often arrive fluent and confident; see [Why the review gate is structural](why-review-gate-is-structural.md). |
| The cost model is inverted | A wrong high-confidence output in Memoria becomes durable, cited knowledge rather than a wasted run. |

The real insight in that ablation — that gating everything is worse than gating well — Memoria keeps, but spends on the other side: **make each review cheaper, not fewer reviews**. A better Peer-reviewer (pre-verified material, structured evidence chains) lets the human review faster without removing the human from the loop.

---

## Why code could be the exception — and why none exists today

Code is the one domain where the three preconditions could hold:

| Precondition | Code analogue |
| --- | --- |
| Monotonic metric | Tests, runtime, or coverage improve or they do not. |
| Reversible change | Git can restore the previous state. |
| Independent experiment | One code experiment need not depend on another's conclusion. |

So a bounded code experiment loop could be admissible in principle.

**But no autonomy exception exists anywhere in the current system** ([checked means checks passed, not a human verdict](https://github.com/eranroseman/memoria-vault/blob/main/design-history/15-alpha.15.md) and [alpha.19 code-output lane](https://github.com/eranroseman/memoria-vault/blob/main/design-history/19-alpha.19.md)). The Engineer posture does not grant Memoria terminal, file, or execution capability. It cannot run a test suite or a keep/revert loop; it scaffolds the code handoff, records provenance, and points at an external agent the PI reviews. No operation carries an autonomous keep/revert loop.

The synthesis gate remains structurally untouched. The request envelope,
trusted-writer checks, read barrier, and optional adapter policy hook still block
unchecked machine output from bypassing required checks or pretending to carry
PI approval. Whether to admit a
bounded code-experiment loop will be revisited only when the
external-coding-agent path is defined beyond the current project handoff — and
reopening it requires a superseding decision, not an incremental relaxation.

---

## What this implies in practice

The design produces a bounded, phase-gated, human-in-the-loop operating cadence:

- Operations propose, classify, draft, and verify — but do not own PI judgment.
- Scheduled and overnight operations create requests and attention. Checked
  materialization can occur only through declared worker checks; PI disposition
  remains separate attention state.
- The discovery loop can run autonomously (finding and ingesting candidates) because the human reviews candidates before they enter the canonical vault.
- The cost discipline ("$1–3/day API budget for the nightly loop") matters because there's no scalar payoff to optimize against. Budget discipline replaces metric discipline.

---

## Where Memoria sits

[Chen 2026](../../reference/bibliography.md#chen2026copilots)'s (*From Copilots to Colleagues*) five-level taxonomy: L1 (autocomplete) → L2 (multi-step, human approval per step) → L3 (multi-step autonomous, human-set strategy, per-batch review) → L4 (self-directed within a domain) → L5 (fully self-directed).

Memoria is L3. Operations execute multi-step work unattended within request and
manifest ceilings. The human sets the strategy (`steering.md`,
`screening-protocol.md`) and the review gate blocks unchecked or unwarranted
promotion from entering checked readers. L4 requires autonomous keep/revert on
synthesis; L5 requires self-directed agenda-setting. Both fail the
preconditions test for knowledge work.

---

## Related

- Why the review gate is structural: [Why the review gate is structural](why-review-gate-is-structural.md)
- The intellectual foundations of this position: [Intellectual foundations](../foundations/intellectual-foundations.md)
- Borrow/adapt/ignore table: [Pattern provenance table](../../reference/pattern-provenance.md)
