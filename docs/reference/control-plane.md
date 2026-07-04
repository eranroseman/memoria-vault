---
title: Control plane reference
parent: Vault data model
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
