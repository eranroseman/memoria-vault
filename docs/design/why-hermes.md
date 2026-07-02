---
title: Why Hermes
parent: Design Book
grand_parent: Developers
nav_order: 14
---

# Why Hermes

Memoria's core runtime is the standalone CLI/engine. [Hermes Agent](https://hermes-agent.nousresearch.com/) (Nous Research) remains an optional adapter for users who want Hermes profiles, Kanban, dispatcher, cron, and API server surfaces around the same vault. This page explains why the adapter exists, what Hermes provides, and where the Memoria/Hermes boundary falls.

If Memoria is *what you keep* — the vault, the knowledge, the schema — the standalone CLI/engine is the required mover. Hermes can add a second operating surface for profile-based and board-based work.

---

## What Hermes provides

The optional adapter contributes four runtime properties:

| Adapter need | Hermes feature | Memoria overlay |
| --- | --- | --- |
| Durable task state | Kanban board (`kanban.db`) | Review metadata on cards. |
| Role separation | Profiles with lanes | Adapter-local mapping onto Memoria requests and operation ceilings. |
| Background execution | Dispatcher | Routing rules, not an Orchestrator agent. |
| Controlled integration | Memory, MCP, API server | Policy gate, request rows, and programmatic triggers. |

Memoria supplies the *conventions on top*: the review-gate overlay in card
`metadata`, the policy gate that gates writes, request mapping, and the workspace
schema. None of those require modifying Hermes, and alpha.14 does not ship
installed Hermes profile packages.

---

## Why not build our own runtime

A bespoke Hermes-like adapter would be a large, ongoing engineering commitment whose hardest parts — durable board state across crashes, atomic card claiming, retry semantics, memory tiers, and an MCP host — are exactly what Hermes already solves. Reimplementing them would produce a worse copy and a maintenance burden, the same reasoning that keeps the [Engineer](../explanation/profiles/engineer.md) MCP-only rather than a reimplementation of an external coding runtime.

Keeping the adapter close to stock `hermes` tooling lets the board work with a standard Hermes install, and Memoria's overlay lives in `metadata` that Hermes treats as opaque (see [the card schema](../explanation/kanban-board/honesty-card.md)). The cost of the adapter is dependency on an external runtime's release cadence and conventions; the benefit is that Memoria does not spend its core design budget reimplementing a second board/runtime surface.

This is a deliberate **borrow** in the [pattern-provenance](why-pattern-provenance.md) sense: Hermes's persistent-Kanban-plus-worker-lanes pattern is adopted wholesale; what Memoria declines from other runtimes is, e.g., chat-as-substrate (AutoGen) and sandbox-vs-host permission models (OpenHands), because those route durable state or permissions through the wrong layer.

---

## The adapter API server

In the standalone runtime, programs connect through CLI commands, file changes, and external schedulers. With the Hermes adapter installed, Hermes's API server adds another programmatic surface for file watchers, Zotero hooks, git hooks, calendar integrations, or cross-machine dispatch. The PI may use Obsidian for daily action; CLI remains the required channel ([Interaction channels](../explanation/architecture/interaction-channels.md)).

The API grants no extra power. Every write still passes through the policy gate, so the caller has only the permissions of the profile it acts as. See [Policy gate](../reference/policy-mcp.md) and [Hermes CLI](../reference/hermes-cli.md#api-server).

---

## The Memoria / Hermes boundary

| Concern | Owned by |
| --- | --- |
| Standalone CLI/engine, SQLite state, trusted writer | Memoria |
| Board state machine, dispatcher, retries | Hermes adapter |
| Profile mechanism (identity, model routing, lanes) | Hermes adapter |
| Native memory tiers, MCP host, API server | Hermes adapter |
| Review-gate overlay and machine recommendation | Memoria (request/attention metadata) |
| Write-gating policy gate | Memoria (plugs into Hermes's MCP interface) |
| Capability manifests and operation policy | Memoria |
| The vault, schema, and document types | Memoria |

The rule of thumb: **Memoria must run without Hermes; when Hermes is installed, Hermes moves adapter work and Memoria still decides what work means and what may become canonical.**

---

## Related

**Explanation**

- What Hermes coordinates — the layered architecture: [Why the architecture is layered](why-layered-architecture.md)
- The request state machine: [Request states and the review gate](../explanation/kanban-board/states.md)
- The attention prompt shape: [The honesty prompt](../explanation/kanban-board/honesty-card.md)
- The interaction channels (Obsidian, CLI, Telegram): [Interaction channels](../explanation/architecture/interaction-channels.md)

**Reference**

- What the API's writes pass through: [Policy gate](../reference/policy-mcp.md)
- Hermes admin commands (reference): [Hermes CLI](../reference/hermes-cli.md)
