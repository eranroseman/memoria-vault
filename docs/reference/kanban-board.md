---
title: Kanban board reference
parent: Vault data model
grand_parent: Reference
---

# Kanban board reference

Alpha.14 does not use a Hermes-native Kanban board as the core control plane.
The shipped control plane is the operation request table in
`.memoria/memoria.sqlite`, surfaced through the `memoria request ...`,
`memoria workspace ...`, and `memoria attention ...` commands.

Legacy board exporters and metrics readers may still consume historical board
logs for compatibility with old data, but new work should be modeled as
operation requests with input refs, output intents, precondition hashes, status,
and journal entries.

## Current Commands

```bash
memoria request list --workspace <workspace>
memoria request show --workspace <workspace> <request-id>
memoria request retry --workspace <workspace> <request-id>
memoria request cancel --workspace <workspace> <request-id>
memoria workspace run --workspace <workspace>
memoria workspace recover --workspace <workspace>
memoria attention list --workspace <workspace>
```

## WIP Limits

Alpha.14 does not enforce Hermes board WIP limits. Concurrency belongs to the
standalone engine/runner and any operator-managed scheduler that invokes it.

## Related

- CLI command surface: [CLI](cli.md)
- Operation manifests: [Operations](operations.md)
- Runtime telemetry examples: [Telemetry logs](telemetry-logs.md)
