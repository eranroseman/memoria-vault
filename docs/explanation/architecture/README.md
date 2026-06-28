---
title: Architecture
parent: Explanation
nav_order: 1
has_children: true
permalink: /explanation/architecture/
---

# Architecture

Memoria is **seven layers** ([ADR-46](../../adr/46-seven-layer-architecture.md)): the **PI** (the human — Principal Investigator), the **Interface** (the Obsidian UI), the **Co-PI** (the one conversational agent), **Tasks** (the kanban board and its background lanes), **MCP** (the policy boundary), the **Operations** (deterministic mechanisms), and the **Vault** (the files — the knowledge itself). One flow rule governs the stack: **decisions flow down, information flows up.**

The shared terms behind this section are defined in [Home](../../README.md).

```text
L1  PI          the human — the only actor who promotes to canonical
L2  Interface   the Obsidian UI: Home, dashboards, Inbox, Library/Knowledge/Project spaces
L3  Co-PI       the permanent conversational agent (Agent Client pane); read-only, delegates writes
L4  Tasks       ephemeral agent lanes + the kanban board + cards
L5  MCP         the policy boundary — agents reach operations and the Vault only through it
L6  Operations     deterministic mechanisms: ingest · search · clustering · sweeps · Linter
L7  Vault       the files & folders — durable knowledge
```

## Three actor-kinds

Three kinds of actor work across the structural layers:

| Actor-kind | Who | Trait |
| --- | --- | --- |
| **PI** | the human (L1) | judgment; the only actor who promotes to canonical |
| **Agents** | the Co-PI (L3) + the Task lanes (L4) | posture + LLM judgment; propose, never dispose |
| **Operations** | ingest · search · clustering · sweeps · Linter (L6) | deterministic, no posture; never on the board |

The "is it an agent or an operation?" question is decided by posture and LLM judgment, not invocation style — deterministic work never occupies a board lane. Agents propose and only the PI disposes; why that gate is structural rather than a convention is [Why the review gate is structural](../../design/why-review-gate-is-structural.md).

## The layering binds the agent write-path only

The strict each-layer-depends-only-on-the-one-below contract holds along the **agent write-path** (Co-PI → Tasks → MCP → Operations/Vault). The PI and trusted automation are **direct edges, not rungs**: the PI edits the Vault directly in Obsidian, and cron, CI, and the PI invoke operations directly. Read the stack as a dependency *order*, not a claim that every actor traverses all seven layers.

**MCP is a policy gate, not an execution sandbox.** The MCP layer validates every agent request — allow-listing tools, scoping writes, rate-limiting, logging — before it touches the Vault or an external API. It does not confine processes; the honest phrase is *policy-sandboxed via MCP*. Under the solo, local premise the threat is *wrong writes*, not tenant escape, and the policy gate plus propose-not-dispose, the gated zones, the audit log, and git history cover it. Execution isolation is deferred until untrusted third-party code is actually run.

## Documents in this section

| Page | What it covers |
| --- | --- |
| [The vault](vault.md) | The vault's category folders, type homes, gated zones, archived-as-state, and how Bases and the Linter keep it sound. |
| [The memory model](memory-model.md) | The memory substrates — their scope, owner, and lifespan — and why the Co-PI is the sole memory carrier. |
| [Interaction channels](interaction-channels.md) | The interaction surfaces — Obsidian, CLI, Telegram — and how the Inbox's graded loudness routes signals. |
| [Session logging](session-logging.md) | What each agent session records, and why the audit log and session summaries stay separate. |
| [Telemetry architecture](telemetry-architecture.md) | Why audit, analytics, and diagnostics are separate planes with different retention and content rules. |

## Where to go next

- **Why the architecture is layered**, and the research behind it → [Why the architecture is layered](../../design/why-layered-architecture.md)
- **The agents that occupy L3 and L4** → [Profiles](../profiles/README.md)
- **The deterministic L6 operations** → [Operations](../operations.md)
- **The board state machine** under the Tasks layer → [Kanban board](../kanban-board/README.md)
