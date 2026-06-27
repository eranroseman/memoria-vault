---
title: Telemetry architecture
parent: Architecture
nav_order: 6
---

# Telemetry architecture

Memoria telemetry is split into three planes because the same event stream cannot
serve audit, product-health, and debugging needs without leaking data or losing
forensic value. This page explains the operating model. Exact schemas live in
[Telemetry log schemas](../../reference/telemetry-logs.md); the decisions are
[ADR-104](../../adr/104-telemetry-three-planes.md),
[ADR-105](../../adr/105-diagnostic-plane.md), and
[ADR-106](../../adr/106-cost-and-disposition-capture.md).

| Plane | What it answers | Where it lives |
| --- | --- | --- |
| **Audit** | Did an authorized write happen, and what changed? | Vault audit log plus session digests. |
| **Analytics** | How is the system performing over time? | Content-free event streams and derived metric notes. |
| **Diagnostic** | Why did Memoria-side code fail? | Local OS state, outside the vault and outside Git. |

## How the planes differ

The audit plane is permanent and content-free. It records write decisions and
hashes so the PI can trace what changed without storing note content in the log.

The analytics plane is also content-free, but it is optimized for trends:
throughput, cost, attention, board state, eval results, and drift. Dashboards read
those projections; they are not a second source of truth.

The diagnostic plane is disposable and private. It captures Memoria-side Python
failures with enough detail to debug, but it stays outside the vault so support
bundles can be reviewed and redacted before sharing.

## Join key

When a telemetry event belongs to delegated work, `task_id` is the join key across
board state, costs, dispositions, and diagnostics. When no card exists, the event
is intentionally local to its plane.

## Related

- Exact event and metric schemas: [Telemetry log schemas](../../reference/telemetry-logs.md)
- Log inventory: [Telemetry & logs](../../reference/telemetry.md)
- Audit/session digest model: [Session logging](session-logging.md)
