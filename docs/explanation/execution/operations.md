---
title: Operations — the deterministic layer
parent: Execution
grand_parent: Explanation
nav_order: 1
has_children: false
permalink: /explanation/execution/operations/
---

# Operations — the deterministic layer

Operations are Memoria's deterministic mechanisms. They ingest, lint, search,
sweep, clean up, and measure without adopting an agent posture. An operation
should produce the same result for the same input; anything requiring a stance,
judgment, or recommendation belongs to an agent or to the PI.

Operations do not occupy board lanes. They run through the CLI,
operator-managed scheduled jobs, CI, or optional adapters that call the same
runtime package. Their findings may surface as attention projections, but the
operation itself is not a queue-owning agent.

## Invocation rule

The path follows the caller, but the authority does not change. CLI work,
operator-managed scheduled work, CI, and optional adapters all use the same
runtime package and must end at the same worker/trusted-writer boundary when
they materialize vault state.

Processing, integrity, telemetry, and maintenance operations are runtime package
entry points. Optional adapters are transport edges, not implementation owners.

## Related

- Exact entry points and responsibilities: [Operations](../../reference/commands-and-transports/operations.md)
- The architecture layer operations occupy: [Architecture](../architecture/README.md)
- The vault operations maintain: [The vault](../architecture/vault.md)
