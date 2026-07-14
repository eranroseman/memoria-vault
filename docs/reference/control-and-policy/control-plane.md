---
title: Control plane reference
parent: Control and policy
nav_order: 1
grand_parent: Reference
---

# Control plane reference

The shipped control plane is the operation request table in
`.memoria/memoria.sqlite`, surfaced through the `memoria request ...`,
`memoria workspace ...`, and `memoria attention ...` commands.

## Current Commands

```bash
memoria request list --workspace <workspace>
memoria request show --workspace <workspace> <request-id>
memoria request answer --workspace <workspace> --idempotency-key <new-key> <request-id> key=value
memoria request amend --workspace <workspace> --idempotency-key <new-key> <request-id> key=value
memoria request retry --workspace <workspace> <request-id>
memoria request cancel --workspace <workspace> <request-id>
memoria request resume --workspace <workspace> <request-id>
memoria workspace run --workspace <workspace>
memoria workspace recover --workspace <workspace>
memoria attention list --workspace <workspace>
```

Request controls are PI-only.

| Control | Current contract |
| --- | --- |
| `answer` / `amend` | Require a new idempotency key and a non-running operation request. They create one pending, PI-attributed successor, bind the source in provenance and causal references, and omit the source schedule. A pending source becomes `cancelled` as superseded; a terminal source keeps its status and gains the successor marker. The source envelope never changes. |
| `cancel` | Changes only `pending` to `cancelled`. Running and terminal requests are rejected. |
| `retry` | Changes `failed` or explicitly PI-cancelled work back to `pending`. A superseded request cannot be retried. |
| `resume` | Claims and runs only `pending` work. |

A source has at most one successor. Repeating the same answer or amendment with
the same key and content returns that successor; changed content or a second
successor conflicts. An amendment cannot change an ID, reference, path, target,
or other scope-bearing field. Submit a new original operation when scope must
change. Integrity-only operations cannot be copied into a PI successor. If a
state transition commits but its lifecycle-event append is interrupted, an
exact repeat appends that one missing event without creating another successor
or reopening work that has since finished.

The local CLI's `--actor` value records declared provenance; it does not
authenticate a caller. Keep the raw CLI PI-owned. Agent integrations use HTTP
or MCP, which bind their request actor to `agent`.

## Actor Authority Guard

A fixed subset of operations requires a specific actor before the worker will
run them at all. `_require_operation_actor` is the first check inside
`_run_operation_job` — it runs before any payload validation. A mismatched
actor fails the job with `"{operation_id} requires {label} actor authority"`
and the rejected job appends zero `event_log` rows.

| Required actor | Operations |
| --- | --- |
| `pi` | `acknowledge-attention`, `resolve-attention`, `record-copi-interview`, `curate-note-candidate`, `curate-note-link`, `mark-checked`, `update-work`, `frame-paper`, `promote-draft-passage`, `cascade-rollback` |
| `integrity` | `trace-integrity-scan`, `observe-pi-edits` |

## WIP Limits

The standalone runtime does not enforce external board WIP limits. Concurrency
belongs to the standalone engine/runner and any operator-managed scheduler that
invokes it.

## Related

- CLI command surface: [CLI](../commands-and-transports/cli.md)
- Operation manifests: [Operations](../commands-and-transports/operations.md)
- Runtime telemetry examples: [Telemetry & logs](../pipelines-and-io/telemetry.md#log-schemas)
