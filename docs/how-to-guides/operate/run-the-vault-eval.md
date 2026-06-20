---
title: Run the vault eval
parent: Operate
nav_order: 8
---

# Run the vault eval

Run Memoria's system-level evaluation on demand — dispatch the gold-set tasks, let the lanes work them, and score the results — instead of waiting for the quarterly cron. The eval measures whether the *deployed system* finds, extracts, links, and verifies correctly on your vault; its verdict is diagnostic, never gating. For the gold set, the metrics, and the result contract, see [Vault eval](../../reference/vault-eval.md).

## When to run it by hand

- After installing a fresh release vault or changing profiles, to confirm capability didn't regress
- When the eval-trend dashboard shows a dip you want to reproduce immediately
- To smoke-test a fresh vault once the gold-set papers (Transformer, BERT, ResNet, Adam, Dropout) are ingested

## Prerequisites

- The gold-set papers ingested — the shipped tasks reference well-known papers so they work on any vault once those are present
- The board and the five profiles running (the eval reuses board dispatch and the lane → profile map)

## Steps

**1. Preview the dispatch.** See which `lifecycle: current` gold tasks would enqueue, creating nothing:

```bash
cd <vault>
python .memoria/operations/telemetry/eval/eval_dispatch.py --vault . --dry-run
```

**2. Dispatch the cards.** One idempotent card per gold task, on its owning lane. The idempotency key is per `(task, quarter)`, so re-running inside the same quarter converges to one card per task rather than duplicating:

```bash
python .memoria/operations/telemetry/eval/eval_dispatch.py --vault .
```

**3. Let the lanes run the cards.** Each lane works its eval card under the non-committing contract — scratch-only writes, results reported on the card; a run never mutates the vault. Give the board time to drain (`hermes kanban list` to watch).

**4. Score the run.** The deterministic, zero-LLM scorer reads the cards' reported result blocks and computes only what each result makes computable — no faked scores:

```bash
python .memoria/operations/telemetry/eval/eval_score.py --vault .                    # current quarter
python .memoria/operations/telemetry/eval/eval_score.py --vault . --quarter previous # what the cron scores
```

Add `--k <n>` to change the recall window (default 3) and `--dry-run` to compute without appending to the log.

**5. Read the trend.** Open the **eval-trend** dashboard (`system/dashboards/eval-trend.md`) — it renders the newest run per quarter plus the latest run's per-task breakdown ([Dashboards](../../reference/dashboards.md)).

## Verify

- `system/metrics/eval/runs.jsonl` has a new line (timestamp, quarter, k, per-task records, per-metric aggregates) — written only when at least one card reported a result block
- The eval-trend dashboard shows the run, with `recall@k` / `support-rate` / `FAMA-clean` per task
- A task whose card reported no machine-readable result shows as **unscored** — never a faked score
- `system/eval/last-run.md` reflects the dispatch you just ran

## The cron equivalent

The quarterly `memoria-eval` cron does exactly these steps in one pass: it **scores the previous quarter** first (its cards have reported by then), then **dispatches** the new quarter's cards. Running on demand is the same two commands by hand. The schedule and wrapper are owned by [Installer (bootstrap)](../../reference/installer.md).

## Related

- The gold set, metrics, and result contract: [Vault eval](../../reference/vault-eval.md)
- The trend dashboard and metric bands: [Dashboards](../../reference/dashboards.md)
- The sibling deterministic maintenance job: [Run the Linter](run-the-linter.md)
- The cron wiring: [Installer (bootstrap)](../../reference/installer.md)
