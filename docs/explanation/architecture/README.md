---
title: Architecture
parent: Explanation
nav_order: 1
has_children: true
permalink: /explanation/architecture/
---

# Architecture

Memoria alpha.15 is a standalone CLI and engine over a local workspace. The
durable flow is: PI intent enters through CLI commands or file edits, operations
run through the request lifecycle, checked outputs materialize into the
workspace, and the vault keep-set remains readable without the runtime.

The shared terms behind this section are defined in [Home](../../README.md).

```text
L1  PI          the human, using the CLI and editor
L2  CLI         request envelope, stable commands, JSON and exit codes
L3  Engine      queue, worker, checks, read barrier, recovery
L4  Operations  ingest, enrichment, search, sweeps, linter, runner-backed operations
L5  Storage     SQLite graph/ops state, blobs, search state
L6  Vault       Markdown keep-set and generated projections
L7  Adapters    optional editor/API surfaces that call the same engine
```

Who the three actor-kinds are (PI, Agents, Operations), and why the layering
contract binds only the machine write path, are covered in [The
vault](vault.md#actor-kinds-and-the-write-path).

## Documents in this section

| Page | What it covers |
| --- | --- |
| [The vault](vault.md) | The vault's bundle roots, Concept homes, actor-kinds and the write path, and how Bases and the Linter keep it sound. |
| [The memory model](memory-model.md) | The memory substrates — their scope, owner, and lifespan — and why durable memory lives in checked workspace state. |
| [Interaction channels](interaction-channels.md) | The interaction surfaces and how the Inbox's graded loudness routes signals. |
| [Session logging](session-logging.md) | What each agent session records, and why the audit log and session summaries stay separate. |
| [Telemetry architecture](telemetry-architecture.md) | Why audit, analytics, and diagnostics are separate planes with different retention and content rules. |

## Where to go next

- **Why the architecture is layered**, and the research behind it → [Why the architecture is layered](../../design/why-layered-architecture.md)
- **The operation postures** -> [Operation postures](../operation-postures/README.md)
- **The deterministic operations** -> [Operations](../operations.md)
