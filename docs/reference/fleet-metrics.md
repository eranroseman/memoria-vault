---
title: Fleet metrics
parent: Pipelines and I/O
grand_parent: Reference
---

# Fleet metrics

Alpha.15 drops the installed profile/lane/fleet runtime model. There is no
shipped fleet-metrics aggregator and no lane trust-score note is part of the
standalone baseline.

## Current Runtime Signals

| Signal | Source |
| --- | --- |
| Request success/failure | `.memoria/memoria.sqlite` request and job rows |
| Mutating write decisions | `system/logs/audit.jsonl` and runtime policy tests |
| Linter findings | `system/logs/lint-findings.jsonl` from scheduled or manual lint runs |
| Eval results | `system/metrics/eval/runs.jsonl` from `memoria eval run` |
| Diagnostics | `memoria doctor bundle` |

Future dashboards may summarize these standalone signals, but they must read the
CLI/runtime state above rather than reintroducing fleet lanes as a product
authority.
