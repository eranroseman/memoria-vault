---
title: Fleet metrics
parent: Reference
---

# Fleet metrics

`src/.memoria/mcp/metrics_aggregate.py` rolls board history, policy audit rows, lint findings, review dispositions, cost rows, and attention timing into weekly lane-metric notes. These notes are the source queried by the Fleet health dashboard.

## Command

```bash
python src/.memoria/mcp/metrics_aggregate.py --vault <vault>
python src/.memoria/mcp/metrics_aggregate.py --vault <vault> --from-json cards.json
```

`--from-json` supplies a saved board JSON payload for tests/offline runs. All other inputs are read from the vault logs listed below and degrade gracefully when absent.

## Inputs

| Input | Used for |
| --- | --- |
| `system/logs/audit.jsonl` | Mutating policy decisions: write count, deny count, dry-run count, and deny rate. |
| Hermes board / `--from-json` cards | Done/blocked counts, retry totals, time on gate, and expand-to-accept timing when card timestamps are present. |
| `system/logs/lint-findings.jsonl` | Drift incident counts and the weekly lint verdict note. |
| `system/logs/disposition.jsonl` | Accepted, edited, rejected review counts and accept ratio. |
| `system/logs/cost.jsonl` | API spend and token totals. |
| `system/logs/board-transitions.jsonl` | Median operator decision time from `review: requested` to a terminal review state. |
| `system/logs/attention.jsonl` | Obsidian-side PI card-open-to-resolve timing. |
| `system/logs/blind-review-samples.jsonl` | Blind re-review sample counts. |

The aggregator covers the four background lanes only: `memoria-librarian`, `memoria-writer`, `memoria-peer-reviewer`, and `memoria-engineer`. Co-PI and deterministic operations are not lane-metric subjects.

## Trust score

The score starts at `100` and subtracts bounded penalties:

| Signal | Penalty |
| --- | --- |
| Deny rate | `40 * deny_rate` |
| Failure rate | `40 * (1 - success_rate)` |
| Retry rate | `20 * retry_rate`, capped at `30` |
| Drift incidents | `2 * drift_incidents`, capped at `20` |
| Secret hits | `10 * secret_hits`, capped at `30` |
| Review ratio anomaly | `10` when accept ratio is above `0.9` or below `0.2` |

The final score is rounded and clamped to `0..100`. Bands are fixed: `90+` is `healthy`, `70..89` is `watch`, and `<70` is `act`. When the combined sample count is below `5`, the score is still written but the band becomes `insufficient-data`.

`consistency_passk` is currently `null`; repeated-run pass-at-k needs a future harness.

## Outputs

| Path | Shape |
| --- | --- |
| `system/metrics/lane-<lane>-<YYYY-Www>.md` | Weekly lane metric note with frontmatter fields used by dashboards. |
| `system/metrics/lint-verdict-<YYYY-Www>.md` | Weekly lint verdict note when `lint-findings.jsonl` exists. |

Re-running in the same ISO week overwrites the metric notes for that week; source logs remain append-only.

## Related

- Dashboard consumers: [Dashboards](dashboards.md)
- Source log schemas: [Telemetry log schemas](telemetry-logs.md)
- Board projection that creates several inputs: [Board export](board-export.md)
