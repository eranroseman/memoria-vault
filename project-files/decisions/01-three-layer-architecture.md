---
topic: decisions
id: 01
title: Three-layer architecture — board, workers, vault
status: accepted
date: 2026-05-01
supersedes: []
superseded_by: []
---

# ADR-01: Three-layer architecture — board, workers, vault

## Context

Any agent-assisted knowledge system has to manage three concerns simultaneously: what work is in progress, who is executing it, and what stable knowledge has accumulated. The naive approach is to let a single agent manage all three from its own context. This works for short sessions but fails across sessions, across retries, and across handoffs — because none of that state survives when the conversation ends.

## Decision

Memoria separates these three concerns into three distinct layers with explicit boundaries between them:

- **Board layer (Kanban)** — owns active work state. Every task lives as a card until a human approves it. The board persists across sessions; workers re-ground on it rather than relying on conversational memory.
- **Worker layer (Hermes profiles)** — owns execution context. Seven specialist profiles, each with narrow permissions and a clear exit condition. Workers are stateless between cards; all continuity comes from the board or the vault.
- **Vault layer (Obsidian)** — owns settled knowledge. Durable, lifecycle-organized, human-reviewed before promotion to canonical zones.

The policy MCP enforces the boundary between workers and vault at runtime — it is not a naming convention.

## Why

Three independent research systems (Chen et al. 2026, AgentRxiv 2025, PARNESS 2026) reach the same empirical conclusion from different starting points: long-horizon agent work fails when state lives in chat and succeeds when state lives in files. Chen's ablation shows removing the durable-artifact layer costs 6.41 points on PaperBench and 31.82 on MLE-Bench Lite. The three-layer split is the structural form of this finding.

Collapsing any two layers breaks specific guarantees:
- Board + workers collapsed → work state lost at session end; retries duplicate effort
- Workers + vault collapsed → agents write canonical knowledge without review; errors compound
- Board + vault collapsed → task history pollutes the knowledge graph; in-flight and settled notes become indistinguishable

## Consequences

- The board is the shared state machine. Every long-lived task must have a card.
- Workers carry no persistent state between cards. They read from the board and vault; they write to the vault's working zones.
- The vault's canonical zones are structurally protected — no worker can write to them without a human review approval.
- Retries are safe: the card persists, the vault is unchanged, the worker can be re-dispatched from the last known state.

## Alternatives considered

**Single agent with rich prompt context** — loses all state at session end; no structural separation between discovery and synthesis; permissions become the superset of all tasks.

**Chat-as-substrate (AutoGen style)** — state lives in conversation history, which is ephemeral, hard to query, and unsuitable for long-horizon work.
