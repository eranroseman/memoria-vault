---
title: Why Hermes
parent: Design Book
grand_parent: Developers
nav_order: 14
---

# Why Hermes

Memoria's entire execution layer is [Hermes Agent](https://hermes-agent.nousresearch.com/) (Nous Research). The board is Hermes's Kanban, the workers are Hermes profiles, the dispatcher is Hermes's, and the integration endpoint is Hermes's API server. This page explains why Memoria builds *on* a runtime rather than building its own, what Hermes provides, and where the Memoria/Hermes boundary falls.

If Memoria is *what you keep* — the vault, the knowledge, the schema — Hermes is *who moves things*: it carries work between states, between profiles, and between the human and the vault.

---

## What Hermes provides

Memoria needs four runtime properties, and Hermes ships them:

| Memoria need | Hermes feature | Memoria overlay |
| --- | --- | --- |
| Durable task state | Kanban board (`kanban.db`) | Review metadata on cards. |
| Role separation | Profiles with lanes | Five Memoria profile directories and lane ceilings. |
| Background execution | Dispatcher | Routing rules, not an Orchestrator agent. |
| Controlled integration | Memory, MCP, API server | Policy MCP, profile memory rules, and programmatic triggers. |

Memoria supplies the *conventions on top*: the review-gate overlay in card `metadata`, the policy MCP that gates writes, the five profile `SOUL.md`s, and the vault schema. None of those require modifying Hermes — they ride its extension points.

---

## Why not build our own runtime

A bespoke agent runtime would be a large, ongoing engineering commitment whose hardest parts — durable state across crashes, atomic card claiming, retry semantics, memory tiers, an MCP host — are exactly what Hermes already solves. Reimplementing them would produce a worse copy and a maintenance burden, the same reasoning that keeps the [Engineer](../explanation/profiles/engineer.md) MCP-only rather than a reimplementation of an external coding runtime.

Building on Hermes also keeps Memoria compatible with stock `hermes` tooling: the board works with any standard Hermes install, and Memoria's overlay lives in `metadata` that Hermes treats as opaque (see [the card schema](../explanation/kanban-board/honesty-card.md)). The cost of this choice is a dependency on an external runtime's release cadence and conventions; the benefit is that Memoria's design effort goes entirely into the *knowledge* layer, which is where its actual contribution lies.

This is a deliberate **borrow** in the [pattern-provenance](why-pattern-provenance.md) sense: Hermes's persistent-Kanban-plus-worker-lanes pattern is adopted wholesale; what Memoria declines from other runtimes is, e.g., chat-as-substrate (AutoGen) and sandbox-vs-host permission models (OpenHands), because those route durable state or permissions through the wrong layer.

---

## The programmatic surface (the API server)

The API server is where programs connect to Memoria: file watchers, Zotero hooks, git hooks, calendar integrations, or cross-machine dispatch. The PI uses Obsidian for daily action; CLI and Telegram are secondary operator/signal channels ([Interaction channels](../explanation/architecture/interaction-channels.md)).

The API grants no extra power. Every write still passes through the policy MCP, so the caller has only the permissions of the profile it acts as. See [Policy MCP](../reference/policy-mcp.md) and [Hermes CLI](../reference/hermes-cli.md#api-server).

---

## The Memoria / Hermes boundary

| Concern | Owned by |
| --- | --- |
| Board state machine, dispatcher, retries | Hermes |
| Profile mechanism (identity, model routing, lanes) | Hermes |
| Native memory tiers, MCP host, API server | Hermes |
| Review-gate overlay (`review_status`, `agent_recommendation`) | Memoria (card `metadata`) |
| Write-gating policy MCP | Memoria (plugs into Hermes's MCP interface) |
| The five profile `SOUL.md`s and lane-overrides | Memoria |
| The vault, schema, and document types | Memoria |

The rule of thumb: **Hermes moves work; Memoria decides what work means and what may become canonical.**

---

## Related

**Explanation**

- What Hermes coordinates — the layered architecture: [Why the architecture is layered](why-layered-architecture.md)
- The board as a state machine: [Board states and the review gate](../explanation/kanban-board/states.md)
- The honesty-card overlay Memoria adds on top of Hermes: [The honesty card](../explanation/kanban-board/honesty-card.md)
- The interaction channels (Obsidian, CLI, Telegram): [Interaction channels](../explanation/architecture/interaction-channels.md)

**Reference**

- What the API's writes pass through: [Policy MCP](../reference/policy-mcp.md)
- Hermes admin commands (reference): [Hermes CLI](../reference/hermes-cli.md)
