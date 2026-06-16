---
topic: decisions
id: 21
title: L3 autonomy ceiling, structurally enforced (the Coder-lane exception is retired)
status: accepted
date_proposed: 2026-06-01
date_resolved: 2026-06-01
assumes: []
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 21
---

# ADR-21: L3 autonomy ceiling, structurally enforced (the Coder-lane exception is retired)

## Context

How far agent autonomy may extend is the single most consequential constraint in Memoria — it governs every future automation proposal — yet it was only ever argued in prose ([Why Memoria doesn't pursue full autonomy](../explanation/rationale/why-not-autonomous.md), [What Memoria is](../explanation/overview/what-memoria-is.md)) and never recorded as a decision with a fixed anchor. The live question is concrete: [Karpathy](../reference/bibliography.md#karpathy-llm-wiki)'s autonomous keep/revert loop is safe only when three preconditions hold simultaneously — the metric is monotonic, changes are reversible, and experiments are independent. Knowledge synthesis fails all three: synthesis quality is not a scalar, synthesis errors persist and compound across everything that later cites them, and later sources reinterpret earlier ones. Without a recorded ceiling, each new "let the agent just do X overnight" proposal re-litigates this from scratch, and the boundary erodes by increments.

## Decision

Memoria targets **L3 on the [Chen et al. 2026](../reference/bibliography.md#chen2026autonomous) taxonomy** — multi-step autonomous execution under human-set strategy with per-batch review — and enforces that ceiling **structurally, through the policy MCP, not through prompt instructions**. Agents propose, classify, draft, and verify; they never canonize. Every promotion into `30-synthesis/` and `50-deliverables/` routes through the human review gate ([ADR-03](03-structural-review-gate.md)). Scheduled and overnight operations write to `10-inbox/` only. The single exception was the **Coder lane**: code artifacts satisfy all three preconditions (tests are a monotonic scalar, `git reset` makes changes reversible, experiments are independent), so an internal keep/revert experiment loop was admissible there, with outputs landing in the project code scratch and still requiring human review to promote. *(v0.1.0-alpha.2 update — **the exception is retired**: the Coder profile is gone ([ADR-48](48-copi-and-agent-consolidation.md)) and its successor, the Engineer, is MCP-only with no execution capability. **No autonomy exception exists anywhere.** The decision will be revisited only if the code lane / external-coding-agent path grows beyond the current Project gate handoff.)* L4 (self-directed synthesis) and L5 (self-directed agenda-setting) are out of scope by construction.

## Consequences

- Confidence-based autonomy refinements are foreclosed for the synthesis lanes: a future "only escalate low-confidence outputs" proposal is answered by this ADR, not re-argued.
- Budget discipline replaces metric discipline. Because there is no scalar payoff to optimize against, the nightly loop is bounded by a cost ceiling (~$1–3/day) rather than by a quality target.
- The human stays on the critical path for every canonical write. The mitigation for the resulting review load is "make each review cheaper, not fewer reviews" — a better Verifier, pre-verified material, structured evidence chains — never removing the gate.
- *(v0.1.0-alpha.2)* No lane carries an autonomous keep/revert loop. Introducing one anywhere — including a future code lane — requires revisiting this ADR explicitly.
- The discovery loop may run unattended because it only *finds and ingests* candidates into `10-inbox/`; the human reviews candidates before they enter canonical zones, so autonomous discovery does not breach the ceiling.

## Alternatives considered

**Full autonomy (L4/L5) on synthesis.** Rejected: this is what every autonomous research system (AI Scientist, AI co-scientist, CORAL, SciMON, Karpathy Autoresearch) does, and all of them rely on a single keep/revert scalar. No such scalar faithfully measures "is this a well-cited, non-redundant addition to the vault," and in durable knowledge work a wrong-but-kept claim compounds rather than wasting one run.

**Confidence-routing (SmartPause / AutoResearchClaw, [Liu et al. 2026](../reference/bibliography.md#liu2026autoresearchclaw)).** Rejected even though its ablation shows targeted gating beats both full autonomy and dense oversight. Hallucinated citations and fabricated numbers are emitted with high fluency and high confidence — confident-wrong is the failure mode the gate exists to catch, and a confidence signal is gameable by exactly that mode. The real insight (gate well, not everywhere) is kept, but spent on cheaper reviews rather than fewer.

## Related

- **Supporting rationale:** [Why Memoria doesn't pursue full autonomy](../explanation/rationale/why-not-autonomous.md) (the preconditions argument and the Coder exception), [Why the review gate is structural](../explanation/rationale/why-human-gate.md), [What Memoria is](../explanation/overview/what-memoria-is.md) (autonomy-spectrum positioning, "vibe researching").
- **Related decisions:** [ADR-03 structural review gate](03-structural-review-gate.md) (the mechanism that enforces this ceiling); [ADR-07 external coding agent boundary](07-delegate-coding-to-external-agents.md) (the Coder lane this ADR carves the exception for).
- **Proposals bounded by this ADR:** the code-lane keep/revert experiment loop
  tracked in [ADR-61](61-nightly-discovery-loop.md); [Configurable review-gate mode
  (blocking | advisory) for comparison studies](41-configurable-review-gate-mode.md)
  (advisory-mode comparison arm).
- **Source discussion:** retroactively records a decision long embedded in `why-not-autonomous.md` and `what-memoria-is.md`. The reasoning lives in those `why-*` docs and may evolve; the ceiling recorded here does not move without a superseding ADR.
