---
title: Telemetry & logs
parent: Pipelines and I/O
nav_order: 6
grand_parent: Reference
---

# Telemetry & logs

Every signal Memoria records about its own operation, with log inventory and
shared conventions. Audit and analytics logs live under `system/logs/`; the
diagnostic plane lives outside the workspace under the OS state directory.
Rationale: [the vault-eval-benchmark-first publication path](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md),
[measurement and verification harnesses](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md), and
[the content-light diagnostic plane](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md).

## Conventions

- **Format.** One JSON object per line (JSONL). A partial last line is the only
  acceptable corruption. Journal verification ignores that fragment, and the
  serialized reconciliation sweep removes it before restoring complete rows
  from the authoritative event log.
- **Append-only.** Writers append rows; rotation is an explicit authorized
  operation.
- **Time.** Every row carries `timestamp` in ISO-8601 UTC with a trailing `Z`.
- **Identity.** Request-scoped rows carry `request_id`; eval rows use
  `eval_role` for diagnostic role grouping.
- **Encoding.** UTF-8, `ensure_ascii=false`.

## Log inventory

| File | Writer | Cadence | One row = |
| --- | --- | --- | --- |
| `audit.jsonl` | runtime policy gate or optional adapter hook | per gated decision or paired write | one policy decision or before/after write record |
| `lint-findings.jsonl` | linter detector run | per manual or scheduled lint run | one detector finding |
| `sessions/YYYY-MM-DD-HHMM.jsonl` | `session_summary.py` | per summary run | one compact per-session digest file |
| `attention.jsonl` | attention disposition runtime | per attention resolution | one PI outcome over an attention projection |
| `triage.jsonl` | attention/import adapters when present | per triage event | one PI triage decision |
| `system/metrics/eval/runs.jsonl` | `eval_score.py` | per eval score run | one scored eval run |

The authoritative operational state is `.memoria/memoria.sqlite`; logs are
evidence streams and diagnostics, not a second state store.

## Log schemas

### audit.jsonl

The write-gate's decision trail. Its full schema is owned by
[Policy audit log](../control-and-policy/policy-audit-log.md).

Every denied, dry-run, policy-load failure, and paired optional-adapter write
appends a row. Worker-owned CLI mutations write authoritative request evidence
to `event_log` in `.memoria/memoria.sqlite`, with derived per-machine JSONL
exports under `.memoria/journal/`; the audit log is the adapter/write-boundary
evidence stream.

### lint-findings.jsonl

One row per detector finding.

```json
{
  "timestamp": "2026-06-01T02:00:00Z",
  "detector": "fama-exposure",
  "severity": "HIGH",
  "path": "projects/draft-x/notes/n.md",
  "message": "cites superseded claim [[oldclaim]]"
}
```

### sessions/YYYY-MM-DD-HHMM.jsonl

The deterministic session-summary file. It begins with a header row, followed by
one row per touched path.

```json
{"kind": "summary", "timestamp": "2026-06-01T02:00:00Z", "request_count": 4}
{"kind": "path", "path": "notes/n.md", "writes": 1, "denies": 0}
```

### system/metrics/eval/runs.jsonl

One row per `memoria eval run` score pass. The exact metric definitions are in
[Vault eval](../analysis-and-surfaces/vault-eval.md).

```json
{
  "timestamp": "2026-06-01T02:00:00Z",
  "run_id": "eval-2026-06-01",
  "recall_at_k": 0.8,
  "support_rate": 0.75,
  "fama_clean": 1.0
}
```
