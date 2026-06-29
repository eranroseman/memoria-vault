---
topic: decisions
id: 41
title: Configurable review-gate mode (blocking / advisory) for comparison studies
nav_exclude: true
status: accepted
assumes: []
date_proposed: 2026-05-31
date_resolved: 2026-06-19
supersedes: []
superseded_by: []
---

# ADR-41: Configurable review-gate mode (blocking / advisory) for comparison studies

> **Naming.** This is **not** [ADR-14](14-advisor-review-vs-frozen-deliverable.md)'s "advisor-review export" (a live-citation `.docx` for a *human academic advisor* in Word). That concerns deliverables. This proposal concerns the *agent review gate* and exists purely as measurement infrastructure.

> **Verified on-box 2026-06-21.** The hard stop is at the write, not the card
> column. There is no on-box code that refuses a board column advance based on
> `review_status`; the guarantee that matters is enforced by the policy decision
> core, where a review-gated path resolves to `dry_run`/block
> (`src/memoria_vault/runtime/policy/decision.py`). The same wording in ADR-03/77/78 should be
> read this way. The decision stands; only the locus of enforcement is corrected.
> Per AGENTS.md, enforcement is a mechanism, not a label.

## What

A single configurable `review_mode` setting with two values:

- **`blocking`** (default, the only recommended operating mode). Current behavior,
  unchanged: writes into review-gated canonical paths resolve to `dry_run`/block
  until the human approval path performs the promotion.
- **`advisory`** (study-only). The `agent_recommendation` is still written and surfaced but does **not** structurally block — a card may advance/promote without approval. This deliberately removes the safety property.

Three invariants make the mode evidence rather than just a weaker system: (1) the same six-signal instrumentation fires identically in both modes (commensurability is the point); (2) every logged event is stamped with its arm (`review_mode`), set live because the attribution is non-backfillable; (3) the default is `blocking` and advisory must be explicitly, narrowly enabled — per study, time-boxed, ideally within-subject.

## Why

Memoria is designed **blocking-only**, and that is correct as the operating posture ([ADR-03](03-structural-review-gate.md)). But the system's publication thesis — "for knowledge work, structurally blocking human review is the correct commitment" — is a claim of the form "*blocking* beats *advisory*," which is **unfalsifiable without an advisory baseline** measured by the same instrument. No current decision provides a non-gating mode, so the system can measure itself but not against the alternative it claims to beat — the one decision-layer gap between today's design and a completable Path 2/3 study.

## Trade-offs

- **Deliberately downgrades the safety property in the advisory arm** — mitigated structurally by default `blocking`, explicit per-study opt-in, time-boxing, and a clear study scope so advisory can never silently become the standing config.
- **Confound risk:** the operator may behave differently knowing an arm is the "weak" one — mitigated by within-subject design and, where feasible, allocating tasks without foreknowledge.
- **Small implementation cost:** the review-gated write decision becomes
  mode-conditional; one `review_mode` field is added (a `schema_version` bump).
- **Companion metric:** a clean false-promotion-rate measurement also needs a **promotion-reversal event** (distinct from supersession), logged in both arms — small, rides on the same instrumentation.

## When this matters

Committing to the Path 2/3 comparison study. The non-backfillable **attribution sliver already shipped** (alpha.5): the policy audit stamps `review_mode: blocking` and `schema_version: 2` (`policy_mcp.py`). What remains is the `advisory` *behavior* itself — a configurable gate mode — which is not part of the day-1 instrument and is not exercised in ordinary use. Building it is a small deterministic change gated only on wanting the study, not on any missing mechanism.


## Alternatives considered

**Use a generic-LLM-assistant baseline instead of an advisory Memoria variant.** Rejected as the primary baseline: it confounds the gating variable with a different tool, retrieval stack, and UI, so any difference is uninterpretable. Useful only as an optional secondary comparison.

**Build a separate advisory fork / profile set.** Rejected: it duplicates the system, drifts from the blocking config, and — fatally — breaks logger commensurability, the whole reason the comparison is worth running.

**Run Path 2/3 single-arm (blocking only).** Rejected: "blocking beats advisory" cannot be supported by observing the blocking arm alone.

**Stay blocking-only and leave the comparison arm undecided.** Rejected as the standing answer because it leaves the system unable to ever produce the comparative evidence; recorded here so the study-only exception is explicit rather than implicit.

## Related

- **Tracking issue:** [#374](https://github.com/eranroseman/memoria-vault/issues/374) — implementation readiness lives on the issue.
- **Workflows:** [Verify](../how-to-guides/project/verify-and-revise.md), [Promote](../how-to-guides/knowledge/promote-a-claim.md); board dispatch rules.
- **Files:** the card/log schema (`review_mode` field, `schema_version` bump); [Measurement and verification harnesses](62-measurement-and-verification-harnesses.md); the publication-instrumentation track in [ADR-20 publication path](20-publication-path.md).
- **Related decisions:** [ADR-03 structural review gate](03-structural-review-gate.md), [ADR-11 vault-eval](11-vault-eval-maintenance.md), [ADR-14](14-advisor-review-vs-frozen-deliverable.md) (distinct "advisor-review").
- **Source discussion:** publication-path analysis — the Path-2/3 advisory-baseline gap.
