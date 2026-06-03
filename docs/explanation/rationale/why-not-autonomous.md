---
title: Why Memoria doesn't pursue full autonomy
parent: Design rationale
nav_order: 2
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

One tempting refinement: route to the human only when the agent's self-assessed confidence is low (SmartPause, as in AutoResearchClaw — [Liu et al. 2026](../../reference/bibliography.md#liu2026autoresearchclaw)). Their ablation finds targeted gating beats both full autonomy and dense step-by-step oversight.

Memoria declines this approach for two reasons:

**Confident-wrong is the failure mode.** Hallucinated citations and fabricated numbers are emitted with high fluency and high confidence, not with visible hesitation. Confidence-routing would wave through exactly the outputs the gate exists to catch. The gate fires on the signal the agent produces — and that signal is gameable by exactly the failure mode that matters.

**The cost model is inverted.** In a throughput-optimizing autonomous system, the cost of a wrong high-confidence output is a wasted run. In Memoria's vault, the cost is a wrongly-promoted claim that persists and compounds. Confidence-routing is worth the bet when errors are cheap; it isn't when the vault is durable.

The real insight in that ablation — that gating everything is worse than gating well — Memoria keeps, but spends on the other side: **make each review cheaper, not fewer reviews**. A better Verifier (pre-verified material, structured evidence chains) lets the human review faster without removing the human from the loop.

---

## The Coder exception

The Coder lane operates differently. Code artifacts have:

- **Monotonic metrics**: tests pass or fail; runtime either improves or doesn't; coverage rises or falls.
- **Reversible changes**: `git reset` recovers the diff; the next run starts from known state.
- **Independent experiments**: one code experiment doesn't depend on the conclusions of another.

All three preconditions hold for Coder work. An autonomous experiment loop — where the Coder profile (or an external coding agent it delegates to) iterates against a test suite, measures results, and keeps or reverts — is admissible for code.

The constraints are narrow by design:

- The work is in the Coder lane only — not Librarian, Writer, Verifier, Mapper, Socratic, or Linter.
- The success criterion is a verifiable scalar that exists before the loop starts — a test suite, a benchmark, a coverage threshold. Not a metric the agent proposes mid-run.
- Outputs land in `40-workbench/<project>/06-code/experiments/` and require human review to promote into working project code. The keep/revert loop is internal to the experiment; the promotion decision still routes through the human review state.

The synthesis gate remains structurally untouched. The policy MCP's review-gated-zone deny rule still blocks writes to `30-synthesis/` and `50-deliverables/`. The Coder's autonomy operates inside zones it has always been permitted to write to.

---

## What this implies in practice

The design produces a bounded, stage-gated, human-in-the-loop operating cadence:

- Agents propose, classify, draft, and verify — but do not canonize.
- Scheduled and overnight operations write to `10-inbox/` only. Promotion is always synchronous with human attention.
- The discovery loop can run autonomously (finding and ingesting candidates) because the human reviews candidates before they enter the canonical vault.
- The cost discipline ("$1–3/day API budget for the nightly loop") matters because there's no scalar payoff to optimize against. Budget discipline replaces metric discipline.

---

## Where Memoria sits

Chen 2026's five-level taxonomy: L1 (autocomplete) → L2 (multi-step, human approval per step) → L3 (multi-step autonomous, human-set strategy, per-batch review) → L4 (self-directed within a domain) → L5 (fully self-directed).

Memoria is L3. The seven profiles execute multi-step work unattended within a card. The human sets the strategy (`research-focus.md`, `screening-protocol.md`) and the review gate blocks every promotion. L4 requires autonomous keep/revert on synthesis; L5 requires self-directed agenda-setting. Both fail the preconditions test for knowledge work.

---

## Related

- Why the review gate is structural: [Why the review gate is structural](why-human-gate.md)
- The intellectual foundations of this position: [Intellectual foundations](../overview/intellectual-foundations.md)
- Full borrow/adapt/ignore table: [Pattern provenance: borrow, adapt, ignore](why-pattern-provenance.md)
