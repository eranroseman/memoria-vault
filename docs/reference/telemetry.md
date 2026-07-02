---
title: Telemetry & logs
parent: Pipelines and I/O
grand_parent: Reference
---

# Telemetry & logs

Every signal Memoria records about its own operation, with log inventory and
shared conventions. Audit and analytics logs live under `system/logs/`; the
diagnostic plane lives outside the workspace under the OS state directory.
Rationale: [ADR-20](../adr/20-publication-path.md),
[ADR-62](../adr/62-measurement-and-verification-harnesses.md), and
[ADR-105](../adr/105-diagnostic-plane.md).

## Conventions

- **Format.** One JSON object per line (JSONL). A partial last line is the only
  acceptable corruption and is dropped on read.
- **Append-only.** Writers append rows; rotation is an explicit authorized
  operation.
- **Time.** Every row carries `timestamp` in ISO-8601 UTC with a trailing `Z`.
- **Identity.** Request-scoped rows carry `request_id`; adapter imports may also
  preserve legacy `task_id` or `lane` fields as data.
- **Encoding.** UTF-8, `ensure_ascii=false`.

## Log Inventory

| File | Writer | Cadence | One row = |
| --- | --- | --- | --- |
| `audit.jsonl` | runtime policy gate or optional adapter hook | per gated decision or paired write | one policy decision or before/after write record |
| `capture-intake.jsonl` | capture/import helpers | per intake | one captured source/input event |
| `patterns.jsonl` | `memoria_vault.runtime.patterns` | per prompt composition | one prompt-operation composition record |
| `lint-findings.jsonl` | linter detector run | per manual or scheduled lint run | one detector finding |
| `sessions/YYYY-MM-DD-HHMM.jsonl` | `session_summary.py` | per summary run | one compact per-session digest file |
| `attention.jsonl` | attention disposition runtime | per attention resolution | one PI outcome over an attention projection |
| `triage.jsonl` | attention/import adapters when present | per triage event | one PI triage decision |
| `linkage.jsonl` | ingest linker | per ingest with ID-missing names | by-name entity collision counters the linker refused to merge |
| `system/metrics/eval/runs.jsonl` | `eval_score.py` | per eval score run | one scored eval run |

The authoritative operational state is `.memoria/memoria.sqlite`; logs are
evidence streams and diagnostics, not a second state store.

## Historical Logs

Old workspaces or archived release artifacts may contain board, cost, blind
review, lane-metric, or cron-heartbeat logs from the pre-alpha.14 Hermes/fleet
runtime. Alpha.14 does not ship the exporters that produced those logs. Current
dashboards and gates should read the runtime request/journal database and the log
inventory above.
