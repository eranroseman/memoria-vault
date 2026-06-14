---
topic: decisions
id: 11
title: vault-eval as a maintenance capability
status: accepted
date_proposed: 2026-05-29
date_resolved: 2026-05-29
assumes: []
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 11
---

# ADR-11: vault-eval as a maintenance capability

> **Implementation status: shipped.** The gold set, the lane dispatcher (`engines/sweeps/eval_dispatch.py`), the non-committing scratch contract, and the quarterly cron shipped first (0.1.0-alpha.1). The **scoring + observability** half landed with [#424](https://github.com/eranroseman/memoria-vault/issues/424): a deterministic scorer (`engines/sweeps/eval_score.py` — the Linter's zero-LLM, report-only discipline, hosted with the sweeps engines beside the dispatcher) reads each card's machine-readable result block off the board, computes recall@k / support-rate / FAMA, appends per-run scores to `system/metrics/eval/runs.jsonl`, and the `eval-trend` dashboard renders the trend. The lane's rubric self-score on the card is recorded for comparison, never aggregated.

## Context

`vault-eval` (an eval-harness scaffold) is Memoria's system-level evaluation — a small hand-curated gold set per workflow that measures whether the *deployed system* finds, verifies, answers, and remembers correctly *on this vault*, as opposed to off-the-shelf benchmarks that score a model on a foreign corpus (see [Measurement and verification harnesses](62-measurement-and-verification-harnesses.md)). To be useful it must run against the live profiles and live with the vault, not persist as an external script. The question is how to host it without standing up a parallel subsystem; it splits into three sub-decisions — who owns it, whether it gates, and where the gold set lives.

## Decision

Memoria runs `vault-eval` as a **diagnostic maintenance capability built from existing machinery**, not a new subsystem:

- **Dispatch (board).** A scheduled `eval` card (quarterly + on-demand) fans each gold task out through the workflow's real profile command — `find` → Librarian, `verify` → the Verifier's `cite-check`, and so on — so the run exercises *deployed* profiles, not mocks.
- **Execution (Policy MCP).** Eval-context profile writes are non-committing: scoped to a scratch path and discarded after scoring, so a run never mutates the vault.
- **Scoring + verdict (Linter).** The Linter scores each run (deterministic metrics — recall@k, support-rate, FAMA — reusing the Verifier's entailment for `verify`), records a per-workflow score, and guards gold-set integrity (a gold item whose target path no longer resolves is a broken-reference finding, like any other).
- **Surfacing (observability).** Results append to `99-system/metrics/eval/` and trend on a dashboard. The verdict is **diagnostic, not gating** — unlike `drift-watch`'s structural FAIL, an eval dip informs the human; it does not pause scheduled work.
- **Gold set (vault).** Gold tasks live in `99-system/eval/` as YAML; they become a dedicated note type only if the [expansion-threshold](README.md) is tripped.

## Consequences

- Reuses board dispatch, the Linter's health-reporting + broken-link detector, the Policy MCP, and the metrics log — no parallel system, and the harness tests the *deployed* profiles on the *real* vault.
- Gold-set rot (renamed/deleted target notes) is caught by machinery already running.
- Requires profiles to support a non-committing eval/dry-run mode — a real implementation cost — and adds one scheduled task, a scratch namespace, and gold-set upkeep.
- Diagnostic-only means a capability regression won't auto-halt work; the human must notice it on the dashboard. This is intentional, per [Measurement and verification harnesses](62-measurement-and-verification-harnesses.md) ("diagnostic, not contract").

## Alternatives considered

**Keep `vault-eval` as an external script outside the runtime** (don't integrate): rejected — it would drift from the deployed profiles, couldn't reuse the health/metrics machinery, and in practice wouldn't be run on a cadence.

**Gate scheduled work on the eval verdict** (like `drift-watch`'s FAIL): rejected — capability scores are noisy and, per `success-metrics.md`, diagnostic not contract; gating on them invites Goodharting and false halts.

**A dedicated eval-runner profile** (not the Linter): rejected for now — eval is a health-reporting concern the Linter already covers, and a new profile violates the expansion-threshold (add a profile only when an existing one is consistently overloaded). Revisit if eval orchestration outgrows the Linter.

**Gold tasks as a note type now**: rejected — premature; YAML in `99-system/eval/` suffices until ≥5 items force a type.

## Related

- **Workflows affected:** [Verify](../how-to-guides/compose/verify-and-revise.md) (the eval reuses `cite-check`); the maintenance/`lint` surface (the Linter scores + reports).
- **Files affected:** [Measurement and verification harnesses](62-measurement-and-verification-harnesses.md), [On-disk layout](../reference/on-disk-layout.md) (`99-system/eval/`, `99-system/metrics/eval/`), the Linter's `structural-detectors.md` and a dashboard (in the starter vault).
- **Related decisions / Depends on:** [ADR-10 claim supersession](10-claim-supersession.md) (the drift gold tasks exercise its FAMA check); [ADR-9 contradictions dashboard](09-contradictions-dashboard.md) and [ADR-8 typed relations](08-typed-relations-frontmatter.md) (shared observability lineage).
- **Source discussion:** [Measurement and verification harnesses](62-measurement-and-verification-harnesses.md) (Observability + Integration); the `vault-eval` scaffold.
