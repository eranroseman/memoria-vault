---
title: Run the vault eval
parent: Operate
grand_parent: How-to guides
nav_order: 8
---

# Run the vault eval

Run Memoria's system-level evaluation on demand — dispatch the gold-set tasks through the local runtime and score reported results — instead of waiting for the scheduled run. The eval measures whether the *deployed system* finds, extracts, links, and verifies correctly on your vault; its verdict is diagnostic, never gating. For the gold set, the metrics, and the result contract, see [Vault eval](../../reference/vault-eval.md).

## When to run it by hand

- After installing a fresh release vault, to confirm capability didn't regress
- When eval metrics show a dip you want to reproduce immediately
- To smoke-test a vault after you have authored local eval-task fixtures

## Prerequisites

- Local `.memoria/eval/*.md` eval-task fixtures authored for the workflows you want to test
- The local runtime installed and `memoria` available on `PATH`

## Steps

**1. Preview the dispatch.** See which `lifecycle: current` gold tasks would enqueue, creating nothing:

```bash
cd <vault>
memoria eval run --workspace . --dry-run --json
```

**2. Dispatch the tasks.** One idempotent local eval task per gold task. The idempotency key is per `(task, quarter)`, so re-running inside the same quarter converges to one task per fixture rather than duplicating:

```bash
memoria eval run --workspace . --json
```

**3. Run the eval work.** Each eval task follows the non-committing contract — scratch-only writes, results reported as JSON; a run never mutates the vault.

**4. Score the run.** The deterministic, zero-LLM scorer reads reported result payloads and computes only what each result makes computable — no faked scores:

```bash
python3 -m memoria_vault.runtime.subsystems.telemetry.eval.eval_score --vault . --from-json results.json
python3 -m memoria_vault.runtime.subsystems.telemetry.eval.eval_score --vault . --quarter previous --from-json results.json
```

Add `--k <n>` to change the recall window (default 3) and `--dry-run` to compute without appending to the log.

**5. Read the trend.** Inspect `system/metrics/eval/runs.jsonl` or an optional
adapter view; the log renders the newest run per quarter plus the latest run's
per-task breakdown ([Dashboards](../../reference/dashboards.md)).

## Verify

- `system/metrics/eval/runs.jsonl` has a new line (timestamp, quarter, k, per-task records, per-metric aggregates) — written only when at least one result payload is reported
- The eval metrics log shows the run, with `recall@k` / `support-rate` / `FAMA-clean` per task
- A task with no machine-readable result shows as **unscored** — never a faked score
- `.memoria/eval/last-run.md` reflects the dispatch you just ran

## Scheduled equivalent

An operator-managed scheduler may call `memoria eval run --workspace . --json`.
Scoring is explicit: run the scorer with `--from-json` once result payloads
exist. The installer does not register a host schedule; see
[Installer (bootstrap)](../../reference/installer.md#host-scheduler-wiring).

## Related

- The gold set, metrics, and result contract: [Vault eval](../../reference/vault-eval.md)
- The trend dashboard and metric bands: [Dashboards](../../reference/dashboards.md)
- The sibling deterministic maintenance job: [Run the Linter](run-the-linter.md)
- Scheduler wiring boundary: [Installer (bootstrap)](../../reference/installer.md)
