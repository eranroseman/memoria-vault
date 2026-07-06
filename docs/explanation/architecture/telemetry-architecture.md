---
title: Telemetry architecture
parent: Architecture
grand_parent: Explanation
nav_order: 5
---

# Telemetry architecture

Memoria telemetry is split into three planes because the same event stream cannot
serve audit, product-health, and debugging needs without leaking data or losing
forensic value. This page explains the operating model. Exact schemas live in
[Telemetry log schemas](../../reference/telemetry-logs.md); the decisions are
[quarantine-and-verify with durable, audit-logged crash recovery](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md),
[the content-light diagnostic plane](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md), and
[Hermes-session-store cost and disposition capture](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md).

| Plane | What it answers | Where it lives |
| --- | --- | --- |
| **Audit** | Did an authorized write happen, and what changed? | Vault audit log plus session digests. |
| **Analytics** | How is the system performing over time? | Content-free event streams and derived metric notes. |
| **Diagnostic** | Why did Memoria-side code fail? | Local OS state, outside the vault and outside Git. |

## How the planes differ

The audit plane is permanent and content-free. It records write decisions and
hashes so the PI can trace what changed without storing note content in the log.

The analytics plane is also content-free, but it is optimized for trends:
throughput, cost, attention, request state, eval results, and drift. Dashboards
read those projections; they are not a second source of truth.

The diagnostic plane is disposable and private. It captures Memoria-side Python
failures with enough detail to debug, but it stays outside the vault so support
bundles can be reviewed and redacted before sharing.

## Join key

When a telemetry event belongs to delegated work, `request_id` is the join key
across request state, costs, dispositions, audit rows, and diagnostics. When no
request exists, the event is intentionally local to its plane.

## Related

- Exact event and metric schemas: [Telemetry log schemas](../../reference/telemetry-logs.md)
- Log inventory: [Telemetry & logs](../../reference/telemetry.md)
- Audit/session digest model: [Session logging](session-logging.md)
