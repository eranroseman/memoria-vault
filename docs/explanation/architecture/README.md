---
title: Architecture
parent: Explanation
nav_order: 1
has_children: true
permalink: /explanation/architecture/
---

# Architecture

Memoria alpha.14 is a standalone CLI and engine over a local workspace. The
durable flow is: PI intent enters through CLI commands or file edits, operations
run through the request lifecycle, checked outputs materialize into the
workspace, and the vault keep-set remains readable without the runtime.

The shared terms behind this section are defined in [Home](../../README.md).

```text
L1  PI          the human, using the CLI and editor
L2  CLI         request envelope, stable commands, JSON and exit codes
L3  Engine      queue, worker, checks, read barrier, recovery
L4  Operations  ingest, enrichment, search, sweeps, linter, runner-backed operations
L5  Storage     SQLite graph/ops state, blobs, qmd state
L6  Vault       Markdown keep-set and generated projections
L7  Adapters    optional editor/API surfaces that call the same engine
```

## Three actor-kinds

Three kinds of actor work across the structural layers:

| Actor-kind | Who | Trait |
| --- | --- | --- |
| **PI** | the human (L1) | judgment; the only actor who promotes to canonical |
| **Agents** | runner-backed operations or optional adapters | posture + LLM judgment; propose, never dispose |
| **Operations** | ingest · search · clustering · sweeps · Linter (L6) | deterministic, no posture; never on the board |

The "is it an agent or an operation?" question is decided by posture and LLM
judgment, not invocation style. Agents propose and only the PI disposes; why
that gate is structural rather than a convention is [Why the review gate is
structural](../../design/why-review-gate-is-structural.md).

## The layering binds the agent write-path only

The strict each-layer-depends-only-on-the-one-below contract holds along the
machine write path: requests enter the engine, operations run under policy, and
checked writes materialize through the worker. The PI may edit Markdown directly;
`memoria workspace scan` observes those edits before checked readers consume
them.

Optional adapters may add pre-tool gates, but the baseline write boundary is the
trusted worker plus staging, read barrier, quarantine, journal, and git history.

## Documents in this section

| Page | What it covers |
| --- | --- |
| [The vault](vault.md) | The vault's bundle roots, Concept homes, write boundary, and how Bases and the Linter keep it sound. |
| [The memory model](memory-model.md) | The memory substrates — their scope, owner, and lifespan — and why the Co-PI is the sole memory carrier. |
| [Interaction channels](interaction-channels.md) | The interaction surfaces and how the Inbox's graded loudness routes signals. |
| [Session logging](session-logging.md) | What each agent session records, and why the audit log and session summaries stay separate. |
| [Telemetry architecture](telemetry-architecture.md) | Why audit, analytics, and diagnostics are separate planes with different retention and content rules. |

## Where to go next

- **Why the architecture is layered**, and the research behind it → [Why the architecture is layered](../../design/why-layered-architecture.md)
- **The agent postures** -> [Profiles](../profiles/README.md)
- **The deterministic operations** -> [Operations](../operations.md)
