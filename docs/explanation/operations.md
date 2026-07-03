---
title: Operations — the deterministic layer
parent: Explanation
nav_order: 4
has_children: false
permalink: /explanation/operations/
---

# Operations — the deterministic layer

Operations are Memoria's deterministic mechanisms. They ingest, lint, search,
sweep, clean up, and measure without adopting an agent posture. An operation
should produce the same result for the same input; anything requiring a stance,
judgment, or recommendation belongs to an agent or to the PI.

Operations do not occupy board lanes. They run through the CLI, scheduled tasks,
CI, or optional adapters that call the same runtime package. Their findings may
surface as attention projections, but the operation itself is not a queue-owning
agent.

## Invocation rule

The path follows the caller:

| Caller | Path |
| --- | --- |
| CLI / PI | Request row, worker operation, trusted writer. |
| Scheduled task / CI | Direct command or scheduled script using the same runtime package. |
| Optional adapter | Runtime policy hook, then CLI/worker request. |

Processing, integrity, cleanup, and telemetry operations are runtime package
entry points. Optional adapters are transport edges, not implementation owners.

## Related

- Exact entry points and responsibilities: [Operations](../reference/operations.md)
- The architecture layer operations occupy: [Architecture](architecture/README.md)
- The vault operations maintain: [The vault](architecture/vault.md)
