---
title: Operations — the deterministic layer
parent: Explanation
nav_order: 88
has_children: false
permalink: /explanation/operations/
---

# Operations — the deterministic layer

Operations are Memoria's deterministic mechanisms. They ingest, lint, cluster,
sweep, clean up, and measure without adopting an agent posture. You run an
operation; you delegate to an agent.

## Invocation rule

The path follows the caller:

| Caller | Path |
| --- | --- |
| Agent profile | MCP facade, then policy-gated operation. |
| PI, cron, CI | Direct command or scheduled script. |

Processing operations expose MCP facades when agents need them. Integrity,
cleanup, and telemetry operations run directly because cron, CI, or the PI are
the callers.

## Why they are not agents

An operation should produce the same result for the same input. That makes it fit
for audit trails, CI gates, scheduled sweeps, and reproducible dashboard metrics.
Anything requiring a stance, judgment, or recommendation belongs to an agent or
to the PI.

## Related

- Exact entry points and responsibilities: [Operations](../../reference/operations.md)
- The architecture layer operations occupy: [Architecture](../architecture/README.md)
- The agents that call operations through MCP: [Profiles](../profiles/README.md)
- The vault operations maintain: [The vault](../architecture/vault.md)
