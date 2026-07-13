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

Request controls are PI-only. Answer and amend create a new PI-attributed
successor request with a new idempotency key. A pending source is cancelled as
superseded; a terminal source remains terminal and is marked as superseded.
They never rewrite the source request envelope. Cancel, retry, and resume
change only request state.

## WIP Limits

The standalone runtime does not enforce external board WIP limits. Concurrency
belongs to the standalone engine/runner and any operator-managed scheduler that
invokes it.

## Related

- CLI command surface: [CLI](../commands-and-transports/cli.md)
- Operation manifests: [Operations](../commands-and-transports/operations.md)
- Runtime telemetry examples: [Telemetry & logs](../pipelines-and-io/telemetry.md#log-schemas)
