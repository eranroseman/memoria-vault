---
title: Telemetry & logs
parent: Pipelines and I/O
grand_parent: Reference
---


# Telemetry & logs

Every signal Memoria records about its own operation, with log inventory and shared conventions. Audit and analytics logs live under `system/logs/`; the diagnostic plane lives outside the vault under the OS state directory. Rationale: [ADR-20](../adr/20-publication-path.md), [ADR-62](../adr/62-measurement-and-verification-harnesses.md), [ADR-105](../adr/105-diagnostic-plane.md).

## Conventions (apply to every log)

- **Format.** One JSON object per line (JSONL). No top-level array, no trailing comma; a partial last line is the only acceptable corruption and is dropped on read.
- **Append-only.** Writers only ever `open(..., "a")`. Rows are immutable events; nothing is rewritten in place. Rotation (truncate-after-archive) is the *only* sanctioned mutation, and only the owning profile may do it (see the `authorized-targeted` auto-fix class in [Policy MCP](policy-mcp.md)).
- **Time.** Every row carries a timestamp in ISO-8601 **UTC** with a trailing `Z` (`2026-06-01T14:23:01Z`). The key is `timestamp` in every log. Never local time — cross-log joins depend on a single clock.
- **Identity.** Card-scoped rows carry `task_id` (board card ID) and `lane` (the assignee profile, e.g. `memoria-writer`). `task_id` is the join key across `board-transitions`, `disposition`, and `cost`.
- **Encoding.** UTF-8, `ensure_ascii=false` — em-dashes and accented author names survive verbatim.

## Log inventory

| File | Writer | Cadence | One row = |
| --- | --- | --- | --- |
| `audit.jsonl` | policy MCP | per gated decision | one policy decision (`allow` / `allow_with_log` / `deny` / `dry_run`) |
| `board-state.jsonl` | `board_export.py` | per export run | a snapshot of per-lane queue counts |
| `board-transitions.jsonl` | `board_export.py` | per export run | one card changing `status` or `review_status` |
| `disposition.jsonl` | legacy/imported review signal | optional | one human review disposition over a work prompt |
| `cost.jsonl` | `board_export.py` | per export run | one completed card joined to a Hermes session cost row |
| `cost-misses.jsonl` | `board_export.py` | per export run | one completed card whose Hermes session join could not be completed |
| `attention.jsonl` | Obsidian QuickAdd | per Inbox resolve action | one PI-side card-open-to-resolve timing sample |
| `triage.jsonl` | Obsidian QuickAdd | per Inbox resolve action | one PI triage decision over an Inbox card |
| `blind-review-samples.jsonl` | `board_export.py` | per export run | one terminal review selected for blind re-review |
| `linkage.jsonl` | ingest `link.py` | per ingest with ID-missing names | by-name entity collision counters the linker refused to merge |
| `cron-heartbeat.jsonl` | cron wrappers | per successful cron job | last-successful-run heartbeat for always-on trigger detection |
| `lint-findings.jsonl` | `memoria-lint` cron | per Linter run | one detector finding |

> **Per-session summaries (`sessions/YYYY-MM-DD-HHMM.jsonl`).** The Linter's `session_summary.py` writes one deterministic digest file per session into `system/logs/sessions/` on the daily lint cron — a header (task, profiles, start/end, action/decision counts) plus one record per touched path. The decision is [ADR-25 (two session logs)](../adr/25-session-logging-two-logs.md); the raw record of session activity remains `audit.jsonl` (below).

Derived, not raw: `system/metrics/lane-<lane>-<period>.md` notes are *computed* by `metrics_aggregate.py` from the logs above; they are reference output, not a capture point. See [their schema](telemetry-logs.md#derived-lane-metric-notes). Likewise derived: `system/metrics/eval/runs.jsonl`, one line per scored vault-eval run, written by `eval_score.py` from the board's eval-card results — schema in [Vault eval](vault-eval.md).

> **Hermes-dependent cost capture.** `board_export.py --cost-doctor` validates the
> pinned Hermes session-store shape before live exports trust cost joins. On a
> completion transition, the exporter reads `hermes kanban show <id> --json` for
> `runs[].metadata.worker_session_id`, joins that ID to
> `~/.hermes/profiles/<lane>/state.db` (`sessions` table), and writes `cost.jsonl`.
> CLI or schema drift fails closed with a clear doctor error. Normal data misses
> such as a missing profile database or missing session row are counted in
> `cost-misses.jsonl` and do not create a bogus zero-cost row.

## Diagnostic plane

Local troubleshooting records for Memoria-owned MCP servers and operations live outside the vault. Exact location, redaction, bundle, and raw-capture rules are in [Diagnostics](diagnostics.md).

## Log schemas

The per-log JSONL schemas and derived metric-note contracts live in [Telemetry log schemas](telemetry-logs.md).

## Related

- Diagnostic plane: [Diagnostics](diagnostics.md)
- Per-log schemas: [Telemetry log schemas](telemetry-logs.md)
- Audit-log writer: [Policy MCP](policy-mcp.md)
