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

## Interaction channels

Memoria has one required PI surface: the CLI over a local workspace. Editor
files are the durable working surface, and optional notification channels can
draw attention to urgent items. They do not become the source of authority.

An optional adapter is not authoritative. Programs may wrap the CLI or watch
files, but the request queue, operation manifests, policy gate, and journal
remain the write boundary.

### Signal routing

Linter findings and attention cards are separate signals. Linter findings have
severity, which orders their output and determines the linter verdict. Operations
that create file-backed Inbox attention assign loudness: quiet and notice cards
remain pull-only, while alert and block cards may push to Telegram when configured.
A planned Maintenance adapter may collect both sources without conflating them.

Routine attention should not push to the phone. If it does, the card's loudness
is wrong.

## Documents in this section

| Page | What it covers |
| --- | --- |
| [The vault](vault.md) | Why durable knowledge lives in the workspace and why writes pass through the worker boundary. |
| [The memory model](memory-model.md) | Why different kinds of memory have different scopes. |
| [Session logging](session-logging.md) | Why audit logs and request summaries stay separate. |
| [Telemetry architecture](telemetry-architecture.md) | Why audit, analytics, and diagnostics are separate planes. |
| [OKF and portability](okf-and-portability.md) | Why Memoria's plain-file bundles outlive the tool and remain portable. |
| [Consistency model](consistency-model.md) | How files and engine state stay honest. |

## Where to go next

- **Why the architecture is layered**, and the research behind it → [Why the architecture is layered](../rationale/boundaries/why-layered-architecture.md)
- **The operation postures** -> [Operation postures](../execution/operation-postures/README.md)
- **The deterministic operations** -> [Operations](../execution/operations.md)
- **CLI commands** -> [CLI](../../reference/commands-and-transports/cli.md)
- **The policy boundary** -> [Policy gate](../../reference/control-and-policy/policy-mcp.md)
