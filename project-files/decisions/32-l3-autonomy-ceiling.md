---
topic: decisions
id: 32
title: L3 autonomy ceiling, structurally enforced, with the Coder-lane exception
status: accepted
date_proposed: 2026-06-01
date_resolved: 2026-06-01
supersedes: []
superseded_by: []
---

# ADR-32: L3 autonomy ceiling, structurally enforced, with the Coder-lane exception

## Context

How far agent autonomy may extend is the single most consequential constraint in Memoria — it governs every future automation proposal — yet it was only ever argued in prose ([why-not-autonomous.md](../../docs/explanation/rationale/why-not-autonomous.md), [what-memoria-is.md](../../docs/explanation/overview/what-memoria-is.md)) and never recorded as a decision with a fixed anchor. The live question is concrete: [Karpathy](../../docs/reference/bibliography.md#karpathy-llm-wiki)'s autonomous keep/revert loop is safe only when three preconditions hold simultaneously — the metric is monotonic, changes are reversible, and experiments are independent. Knowledge synthesis fails all three: synthesis quality is not a scalar, synthesis errors persist and compound across everything that later cites them, and later sources reinterpret earlier ones. Without a recorded ceiling, each new "let the agent just do X overnight" proposal re-litigates this from scratch, and the boundary erodes by increments.

## Decision

Memoria targets **L3 on the [Chen et al. 2026](../../docs/reference/bibliography.md#chen2026autonomous) taxonomy** — multi-step autonomous execution under human-set strategy with per-batch review — and enforces that ceiling **structurally, through the policy MCP, not through prompt instructions**. Agents propose, classify, draft, and verify; they never canonize. Every promotion into `30-synthesis/` and `50-deliverables/` routes through the human review gate ([ADR-03](03-structural-review-gate.md)). Scheduled and overnight operations write to `10-inbox/` only. The single exception is the **Coder lane**: code artifacts satisfy all three preconditions (tests are a monotonic scalar, `git reset` makes changes reversible, experiments are independent), so an internal keep/revert experiment loop is admissible there — but its outputs land in `40-workbench/<project>/06-code/experiments/` and still require human review to promote. L4 (self-directed synthesis) and L5 (self-directed agenda-setting) are out of scope by construction.

## Consequences

- Confidence-based autonomy refinements are foreclosed for the synthesis lanes: a future "only escalate low-confidence outputs" proposal is answered by this ADR, not re-argued.
- Budget discipline replaces metric discipline. Because there is no scalar payoff to optimize against, the nightly loop is bounded by a cost ceiling (~$1–3/day) rather than by a quality target.
- The human stays on the critical path for every canonical write. The mitigation for the resulting review load is "make each review cheaper, not fewer reviews" — a better Verifier, pre-verified material, structured evidence chains — never removing the gate.
- The Coder exception is narrow and must stay narrow: extending an autonomous keep/revert loop to any non-Coder lane is a violation of this ADR and would require superseding it.
- The discovery loop may run unattended because it only *finds and ingests* candidates into `10-inbox/`; the human reviews candidates before they enter canonical zones, so autonomous discovery does not breach the ceiling.

## Alternatives considered

**Full autonomy (L4/L5) on synthesis.** Rejected: this is what every autonomous research system (AI Scientist, AI co-scientist, CORAL, SciMON, Karpathy Autoresearch) does, and all of them rely on a single keep/revert scalar. No such scalar faithfully measures "is this a well-cited, non-redundant addition to the vault," and in durable knowledge work a wrong-but-kept claim compounds rather than wasting one run.

**Confidence-routing (SmartPause / AutoResearchClaw, [Liu et al. 2026](../../docs/reference/bibliography.md#liu2026autoresearchclaw)).** Rejected even though its ablation shows targeted gating beats both full autonomy and dense oversight. Hallucinated citations and fabricated numbers are emitted with high fluency and high confidence — confident-wrong is the failure mode the gate exists to catch, and a confidence signal is gameable by exactly that mode. The real insight (gate well, not everywhere) is kept, but spent on cheaper reviews rather than fewer.

## Related

- **Supporting rationale:** [why-not-autonomous.md](../../docs/explanation/rationale/why-not-autonomous.md) (the preconditions argument and the Coder exception), [why-human-gate.md](../../docs/explanation/rationale/why-human-gate.md), [what-memoria-is.md](../../docs/explanation/overview/what-memoria-is.md) (autonomy-spectrum positioning, "vibe researching").
- **Related decisions:** [ADR-03 structural review gate](03-structural-review-gate.md) (the mechanism that enforces this ceiling); [ADR-07 external coding agent boundary](07-code-agent-attachment.md) (the Coder lane this ADR carves the exception for).
- **Proposals bounded by this ADR:** [PROP-01-code-artifact-autopilot.md](../proposals/PROP-01-code-artifact-autopilot.md) (the keep/revert loop, admissible only within the Coder exception); [PROP-08-configurable-review-gate-mode.md](../proposals/PROP-08-configurable-review-gate-mode.md) (advisory-mode comparison arm).
- **Source discussion:** retroactively records a decision long embedded in `why-not-autonomous.md` and `what-memoria-is.md`. The reasoning lives in those `why-*` docs and may evolve; the ceiling recorded here does not move without a superseding ADR.
