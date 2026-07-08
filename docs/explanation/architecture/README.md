---
title: Architecture
parent: Explanation
nav_order: 1
has_children: true
permalink: /explanation/architecture/
---

# Architecture

Memoria is a standalone CLI and engine over a local workspace. The
durable flow is: PI intent enters through CLI commands or file edits, operations
run through the request lifecycle, checked outputs materialize into the
workspace, and the vault keep-set remains readable without the runtime.

The shared terms behind this section are defined in [Home](../../README.md).
The short version: the PI works through CLI and files; the engine turns requests
into checked or staged workspace state; optional adapters can wrap the engine,
but they do not own the write path.

Who the three actor-kinds are (PI, Agents, Operations), and why the layering
contract binds only the machine write path, are covered in [The
vault](vault.md#actor-kinds-and-the-write-path).

## Documents in this section

| Page | What it covers |
| --- | --- |
| [The vault](vault.md) | Why durable knowledge lives in the workspace and why writes pass through the worker boundary. |
| [The memory model](memory-model.md) | Why different kinds of memory have different scopes. |
| [Interaction channels](interaction-channels.md) | Why the CLI is required and other channels are secondary. |
| [Session logging](session-logging.md) | Why audit logs and request summaries stay separate. |
| [Telemetry architecture](telemetry-architecture.md) | Why audit, analytics, and diagnostics are separate planes. |

## Where to go next

- **Why the architecture is layered**, and the research behind it → [Why the architecture is layered](../../design/boundaries/why-layered-architecture.md)
- **The operation postures** -> [Operation postures](../execution/operation-postures/README.md)
- **The deterministic operations** -> [Operations](../execution/operations.md)
