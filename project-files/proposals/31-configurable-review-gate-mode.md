---
topic: proposals
id: 31
title: Configurable review-gate mode (blocking | advisory) for comparison studies
status: proposed
date_proposed: 2026-05-31
date_resolved:
supersedes: []
superseded_by: []
---

# Proposal 31: Configurable review-gate mode (blocking | advisory) for comparison studies

## Context

Memoria is designed **blocking-only**: review is a structurally enforced state, not an annotation. The human gate is mandatory and promotion never happens silently ([ADR-03](../decisions/03-structural-review-gate.md): the structurally-enforced human review gate, which also keeps claim→reference promotion manual), and dispatch refuses to advance a card past review without `review_status: approved` ([timeline](../operations/timeline.md), steps 4 and 6). This is correct as the *operating* posture — and it is the core of the system's publication thesis.

But that thesis — **"for knowledge work, structurally blocking human review is the correct architectural commitment"** — is the central empirical claim of the system paper (Path 2) and the position paper (Path 3). A claim of the form "*blocking* beats *advisory*" is **unfalsifiable without an advisory baseline to compare against.** The publication-path analysis names exactly this: Path 2's comparison study needs "an advisory-review variant" run against the blocking arm with commensurable instrumentation (see [measurement-and-verification.md](measurement-and-verification.md)).

No current ADR provides a non-gating mode. The system can measure *itself*, but it cannot measure itself *against the alternative it claims to beat*. This is the one decision-layer gap between the existing design and a completable Path 2/3.

> **Naming.** This is **not** ADR-26's "advisor-review export" (a live-citation `.docx` for a *human academic advisor* in Word). That concerns deliverables. This ADR concerns the *agent review gate* and exists purely as measurement infrastructure.

## Decision

Add a single configurable setting, `review_mode`, with two values:

- **`blocking`** (default, and the only recommended operating mode). The current behavior, unchanged: dispatch refuses to advance a card out of `done`/awaiting-review without human `review_status: approved`. This is the production posture and the thesis under test.
- **`advisory`** (study-only). The `agent_verdict` is still written and surfaced, but it does **not** structurally block: a card may advance/promote without `review_status: approved`. This deliberately removes the safety property — so it is **opt-in, time-boxed, and study-scoped**, never a default and never the production posture.

Three invariants make the mode useful as evidence rather than just a weaker system:

1. **The same instrumentation fires identically in both modes.** The five-signal log — suggestion disposition (accept : edit : reject) per profile, operator decision time per review, per-card state-transition timestamps, API cost per card, policy deny reasons — is emitted in `advisory` exactly as in `blocking`. Commensurability is the entire point; a baseline measured by a different instrument is not a baseline.
2. **Every logged event is stamped with its arm.** A `review_mode: blocking | advisory` field is recorded on each card and in the audit log *at event time* — this attribution is non-backfillable and must be set live.
3. **The default is `blocking` and advisory must be explicitly, narrowly enabled** — per study, time-boxed, ideally within-subject (same operator, comparable projects/sources) to isolate the gating variable rather than confounding it with operator or corpus differences.

`advisory` mode is gated on committing to the Path 2/3 comparison study; it is not part of the day-1 instrument and not exercised in ordinary use.

## Consequences

- **Unblocks Paths 2/3 without a parallel system.** The "blocking vs advisory" comparison becomes a config flip on one dispatch rule, not a forked codebase — and because the logger is shared, the two arms produce directly comparable time series.
- **Deliberately downgrades the safety property in the advisory arm.** Mitigated structurally by: default `blocking`, explicit per-study opt-in, time-boxing, and a clear study scope (a branch, a dedicated project, or a marked window) so an advisory run can never silently become the standing configuration.
- **Confound risk: the operator may behave differently knowing an arm is the "weak" one.** Mitigated by within-subject design and, where feasible, allocating tasks to arms without foreknowledge.
- **Small implementation cost.** The Phase-4 dispatch rule that blocks non-approved cards becomes mode-conditional; one `review_mode` field is added to the card/log schema (a `schema_version` bump).
- **Companion metric.** A clean false-promotion-rate measurement also needs a **promotion-reversal event** (a markable "this promotion was later found wrong" signal, distinct from supersession) — logged in *both* arms. It is small and rides on the same instrumentation; tracked here as the comparison's companion, not a separate subsystem.

## Alternatives considered

**Use a generic-LLM-assistant baseline (e.g., ChatGPT-with-files) instead of an advisory Memoria variant.** Rejected as the *primary* baseline: it confounds the gating variable with a different tool, retrieval stack, and UI, so any difference is uninterpretable. It remains useful only as an optional *secondary, external* comparison. The advisory toggle is the one that isolates the single variable the thesis is about.

**Build a separate advisory fork / profile set.** Rejected: it duplicates the system, drifts from the blocking configuration over time, and — fatally — breaks logger commensurability, which is the whole reason the comparison is worth running.

**Run Path 2/3 single-arm (n=1, blocking only, no comparison).** Rejected: the claim "blocking beats advisory" cannot be supported by observing the blocking arm alone. A single-arm study can describe the blocking experience but cannot make the comparative argument the papers rest on.

**Stay blocking-only and defer the question.** Rejected as the standing answer because it leaves the system unable to ever produce the comparative evidence; recorded here as `proposed` precisely so the decision is explicit rather than implicit.

## Related

- **Workflows affected:** [Verify](../../docs/how-to-guides/writing/verify-and-revise.md), [Promote](../../docs/how-to-guides/sources/promote-a-claim.md) (the gate the mode conditions); the board dispatch rules ([timeline](../operations/timeline.md)).
- **Files affected:** the card/log schema (`review_mode` field, `schema_version` bump); [measurement-and-verification.md](measurement-and-verification.md) (the comparison metrics and their definitions); the publication-instrumentation track in [timeline.md](../operations/timeline.md).
- **Related decisions:** [ADR-03 structural review gate](../decisions/03-structural-review-gate.md) (the blocking human gate + no-auto-promotion this makes measurable), [ADR-11 vault-eval](../decisions/11-vault-eval-integration.md) (diagnostic eval the comparison data complements), [ADR-14](../decisions/14-advisor-review-vs-frozen-deliverable.md) (distinct "advisor-review" — deliverables, not the agent gate).
- **Source discussion:** publication-path analysis — the Path-2/3 advisory-baseline gap.
