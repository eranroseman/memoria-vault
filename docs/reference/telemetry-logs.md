---
title: Telemetry log schemas
parent: Pipelines and I/O
grand_parent: Reference
---

# Telemetry log schemas

Exact JSONL schemas for Memoria operational logs. For the inventory,
conventions, and capture posture, see [Telemetry & logs](telemetry.md).

## audit.jsonl

The write-gate's decision trail. Its full schema is owned by
[Policy audit log](policy-audit-log.md).

Every denied, dry-run, policy-load failure, and paired optional-adapter write
appends a row. Worker-owned CLI mutations also write journal/request evidence in
`.memoria/memoria.sqlite`; the audit log is the adapter/write-boundary evidence
stream.

## lint-findings.jsonl

One row per detector finding.

```json
{
  "timestamp": "2026-06-01T02:00:00Z",
  "detector": "fama-exposure",
  "severity": "HIGH",
  "path": "knowledge/projects/draft-x/notes/n.md",
  "message": "cites superseded claim [[oldclaim]]"
}
```

## sessions/YYYY-MM-DD-HHMM.jsonl

The deterministic session-summary file. It begins with a header row, followed by
one row per touched path.

```json
{"kind": "summary", "timestamp": "2026-06-01T02:00:00Z", "request_count": 4}
{"kind": "path", "path": "knowledge/notes/n.md", "writes": 1, "denies": 0}
```

## system/metrics/eval/runs.jsonl

One row per `memoria eval run` score pass. The exact metric definitions are in
[Vault eval](vault-eval.md).

```json
{
  "timestamp": "2026-06-01T02:00:00Z",
  "run_id": "eval-2026-06-01",
  "recall_at_k": 0.8,
  "support_rate": 0.75,
  "fama_clean": 1.0
}
```
