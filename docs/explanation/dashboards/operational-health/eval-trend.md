---
title: eval-trend dashboard
parent: Operational health
nav_order: 3
grand_parent: Dashboards
---

# `eval-trend` dashboard

Tracks whether the deployed system still finds, extracts, links, and verifies correctly *on this vault* — the vault-eval capability trend ([ADR-11](../../../adr/11-vault-eval-maintenance.md)). It matters because capability regressions are silent: a profile prompt drift, a model change, or gold-set rot degrades answers without producing an error anywhere else.

## What it shows

One row per scored quarter, from `system/metrics/eval/runs.jsonl` — the append-only log the deterministic scorer (`eval_score.py`) writes after each eval run. Three aggregate metrics, each 0–1 and higher-is-better:

- **recall@k** — did retrieval surface the gold target citekeys in the top *k*?
- **support-rate** — did the cited evidence resolve to real catalog records, or was it fabricated?
- **FAMA-clean** — was any superseded or archived claim reused (the FAMA failure mode the supersession mechanism makes measurable)?

Below the trend, the latest run breaks out per gold task, including each lane's rubric **self-score** for comparison — recorded, not trusted: only the machine metrics aggregate.

## What it is not

Not a gate. The verdict is diagnostic by design — unlike drift-watch's structural FAIL, an eval dip informs the human and pauses nothing. Capability scores are noisy; gating on them invites Goodharting and false halts ([ADR-11](../../../adr/11-vault-eval-maintenance.md), Alternatives).

It is also not a claim of completeness. A gold task whose card reported no machine-readable result shows as **unscored** — the dashboard is honest about what it could not measure rather than backfilling a number.

## Why the scorer is deterministic

The lanes already self-score against the rubric on their cards, but a self-score is the system grading its own homework. The trend you act on must come from zero-LLM checks against vault state — set membership in the catalog, frontmatter lifecycle on claims — so that a score change means the *system* changed, not the grader.

## Related

- The contract and metric definitions: [Vault eval](../../../reference/vault-eval.md)
- The operational sibling: [fleet-health dashboard](fleet-health.md)
- The decision: [ADR-11](../../../adr/11-vault-eval-maintenance.md)
