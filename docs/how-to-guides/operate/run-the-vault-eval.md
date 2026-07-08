---
title: Run the vault eval
parent: Operate
grand_parent: How-to guides
nav_order: 8
---

# Run the vault eval

Run Memoria's system-level evaluation on demand instead of waiting for the
scheduled run. The eval is diagnostic, never gating.

## When to run it by hand

- After installing a fresh release vault, to confirm capability didn't regress
- When the eval-trend dashboard shows a dip you want to reproduce immediately
- To smoke-test a fresh vault once the gold-set papers (Transformer, BERT, ResNet, Adam, Dropout) are ingested

## Prerequisites

- The gold-set papers ingested
- The local runtime installed and `memoria` available on `PATH`

## Steps

**1. Preview the dispatch.** See which `lifecycle: current` gold tasks would enqueue, creating nothing:

```bash
cd <vault>
memoria eval run --workspace . --dry-run --json
```

**2. Dispatch the tasks.**

```bash
memoria eval run --workspace . --json
```

**3. Run the eval work.**

Each eval task reports results as JSON and does not mutate the vault.

**4. Score the run.**

```bash
python3 -m memoria_vault.runtime.subsystems.telemetry.eval.eval_score --vault . --from-json results.json
python3 -m memoria_vault.runtime.subsystems.telemetry.eval.eval_score --vault . --quarter previous --from-json results.json
```

Add `--k <n>` to change the recall window (default 3) and `--dry-run` to compute without appending to the log.

**5. Read the trend.** Open the **eval-trend** dashboard (`system/dashboards/eval-trend.md`) — it renders the newest run per quarter plus the latest run's per-task breakdown ([Dashboards](../../reference/dashboards.md)).

## Verify

- `system/metrics/eval/runs.jsonl` has a new line (timestamp, quarter, k, per-task records, per-metric aggregates) — written only when at least one result payload is reported
- The eval-trend dashboard shows the run, with `recall@k` / `support-rate` / `FAMA-clean` per task
- A task with no machine-readable result shows as **unscored** — never a faked score
- `.memoria/eval/last-run.md` reflects the dispatch you just ran

## Related

- The gold set, metrics, and result contract: [Vault eval](../../reference/vault-eval.md)
- The trend dashboard and metric bands: [Dashboards](../../reference/dashboards.md)
- The sibling deterministic maintenance job: [Run the Linter](run-the-linter.md)
- Scheduler wiring boundary: [Installer (bootstrap)](../../reference/installer.md)
