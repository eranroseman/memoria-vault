---
title: Board export
parent: Reference
---

# Board export

`src/.memoria/mcp/board_export.py` is the one-way projection from the Hermes Kanban database into vault files and telemetry logs. The Hermes board at `~/.hermes/kanban.db` remains authoritative; the exported files are consumer views for Obsidian dashboards, Inbox Activity, Dataview, metrics aggregation, review prompts, and blocker tickets.

## Command

```bash
python src/.memoria/mcp/board_export.py --vault <vault>
python src/.memoria/mcp/board_export.py --vault <vault> --from-json cards.json
python src/.memoria/mcp/board_export.py --cost-doctor
```

| Option | Contract |
| --- | --- |
| `--vault <vault>` | Required unless `--cost-doctor` is used. Resolves the installed runtime vault root. |
| `--from-json <file>` | Test/offline mode. Reads a saved `hermes kanban list --json` payload instead of invoking Hermes. Cost lookup is skipped in this mode. |
| `--hermes-home <path>` | Overrides `$HERMES_HOME` / `~/.hermes` when joining completed cards to Hermes session rows. |
| `--cost-doctor` | Validates Hermes session-store cost capture and exits without exporting board files. |

Without `--from-json`, the exporter shells out to `hermes kanban list --json`. Completed-card cost rows also join through `hermes kanban show <id> --json` using `runs[].metadata.worker_session_id` and the per-profile Hermes `state.db` session table.

## Outputs

| Path | Shape |
| --- | --- |
| `system/board/<task_id>.md` | One markdown projection per live card for board-state dashboards; the Inbox Activity view shows only in-process statuses. QuickAdd and Co-PI delegation may seed this immediately, and export reconciles it from Hermes. |
| `system/logs/board-state.jsonl` | Queue-depth snapshot, one row per export run. |
| `system/logs/board-transitions.jsonl` | Per-card status and review-state transitions derived from the previous export cache. |
| `system/logs/disposition.jsonl` | Review decisions: `accept`, `edit`, or `reject`. |
| `system/logs/cost.jsonl` | API spend and token counts per completed card when the Hermes session join succeeds. |
| `system/logs/cost-misses.jsonl` | Completed cards whose Hermes session/cost join could not be completed. |
| `system/logs/blind-review-samples.jsonl` | Deterministic sample requests for blind re-review. |
| `inbox/work-prompt-review-*.md` | One PI review prompt for a card that newly reaches `done` with `review_status: requested`; status-only cards stay out of `inbox/`. |
| `inbox/gap-map-corpus.md` | One source-gap card when Map corpus blocks below the calibrated corpus floor. |
| `inbox/work-prompt-map-corpus-blocked.md` | Domain-specific blocked ticket for a Map corpus task that cannot complete. |
| `inbox/work-prompt-blocked-*.md` | Fallback blocked-task prompt when no domain-specific ticket exists. |

`system/logs/.board-state-cache.json` stores the previous card snapshot. The exporter diffs the current board against that cache before saving the new cache, so transition logs are append-only while projected card markdown is refreshed.

## Failure modes

| Failure | Result |
| --- | --- |
| `hermes` is missing from `PATH` and no `--from-json` is provided | The command exits with an explanatory error. |
| `hermes kanban list --json` exits non-zero | The command exits and includes the Hermes stderr text. |
| Cost-capture schema validation fails | The command exits with `[board_export] cost doctor failed`. |
| A completed card cannot be joined to a Hermes session row | Export continues; the miss is written to `system/logs/cost-misses.jsonl`. |

## Related

- Board state machine and review overlay: [Kanban board reference](kanban-board.md)
- Log schemas consumed by the exporter and metrics: [Telemetry log schemas](telemetry-logs.md)
- Derived lane metrics: [Fleet metrics](fleet-metrics.md)
