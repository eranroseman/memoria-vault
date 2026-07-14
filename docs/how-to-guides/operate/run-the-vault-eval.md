---
title: Run the vault eval
parent: Operate
grand_parent: How-to guides
nav_order: 4
---

# Run the vault eval

Run Memoria's system-level evaluation on demand instead of an
operator-managed scheduled run. The eval is diagnostic, never gating.

## When to run it by hand

- After adding or updating local eval-task fixtures
- When the eval log or an optional Eval trend view shows a dip you want to reproduce immediately
- To compare a local workflow against a workspace-authored gold set

## Prerequisites

- At least one `lifecycle: current` markdown eval task under `.memoria/eval/`
  (`memoria init` ships none by default)
- The local runtime installed and `memoria` available on `PATH`

## Steps

**1. Preview the dispatch.** See which `lifecycle: current` gold tasks would
enqueue, creating nothing. A package-seed-only workspace reports zero tasks.

```bash
cd <vault>
memoria eval run --workspace . --dry-run --json
```

**2. Dispatch the tasks.**

```bash
memoria eval run --workspace . --json
```

**3. Run the eval work.**

Each eval task keeps its work in scratch and reports results as JSON; it does
not write Concepts or catalog data. The dispatcher and scorer still update eval
state: `.memoria/eval/last-run.md` and, after scoring, `system/metrics/eval/runs.jsonl`.

**4. Score the run.**

```bash
python3 -m memoria_vault.runtime.subsystems.telemetry.eval.eval_score --vault . --from-json results.json
python3 -m memoria_vault.runtime.subsystems.telemetry.eval.eval_score --vault . --quarter previous --from-json results.json
```

Add `--k <n>` to change the recall window (default 3) and `--dry-run` to compute without appending to the log.

**5. Read the trend.** Inspect `system/metrics/eval/runs.jsonl` or an optional dashboard/editor view. The newest line per quarter carries the trend; the latest run carries the per-task breakdown ([Dashboards](../../reference/analysis-and-surfaces/dashboards.md)).

## Verify

- `system/metrics/eval/runs.jsonl` has a new line (timestamp, quarter, k, per-task records, per-metric aggregates) — written only when at least one result payload is reported
- `system/metrics/eval/runs.jsonl` or your chosen view shows the run, with `recall@k` / `support-rate` / `FAMA-clean` per task
- A task with no machine-readable result shows as **unscored** — never a faked score
- `.memoria/eval/last-run.md` reflects the dispatch you just ran

## Related

- Local gold-task fixtures, metrics, and result contract: [Vault eval](../../reference/analysis-and-surfaces/vault-eval.md)
- Eval metric bands: [Dashboards](../../reference/analysis-and-surfaces/dashboards.md)
- The sibling deterministic maintenance job: [Run the Linter](run-the-linter.md)
- Scheduler wiring boundary: [Installer (bootstrap)](../../reference/system/installer.md)
