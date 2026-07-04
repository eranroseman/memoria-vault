---
title: Kanban board reference
parent: Vault data model
grand_parent: Reference
---

# Kanban board reference

Alpha.15 does not use a Hermes-native Kanban board as the core control plane.
The shipped control plane is the operation request table in
`.memoria/memoria.sqlite`, surfaced through the `memoria request ...`,
`memoria workspace ...`, and `memoria attention ...` commands.

Historical board logs may appear in old ADRs, release scratch, or imported
archives only. Alpha.15 does not ship compatibility readers, exporters, or
migration paths for them; new work is modeled as operation requests with input
refs, output intents, precondition hashes, status, and journal entries.

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

Alpha.15 does not enforce Hermes board WIP limits. Concurrency belongs to the
standalone engine/runner and any operator-managed scheduler that invokes it.

## Related

- CLI command surface: [CLI](cli.md)
- Operation manifests: [Operations](operations.md)
- Runtime telemetry examples: [Telemetry logs](telemetry-logs.md)
