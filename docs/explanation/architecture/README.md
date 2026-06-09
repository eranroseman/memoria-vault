---
title: Architecture
parent: Explanation
nav_order: 2
has_children: true
permalink: /explanation/architecture/
---

# Architecture

Memoria separates three concerns into three layers: a Kanban **board** that orchestrates active work, seven Hermes **profiles** that execute it, and an Obsidian **vault** that stores durable knowledge. The layers connect through explicit handoffs but are never collapsed into one. This section describes what each layer and surface _is_ — the structural pages; the _why_ behind the split (and the research behind it) lives in [Why three layers, not one](../rationale/why-three-layers.md).

```text
┌──────────────────────────────────────────────────────────────────┐
│  Board layer (Kanban) — orchestration and memory of active work  │
│  triage → todo → ready → running → done → archived               │
│  review overlay on done: requested → approved                    │
└──────────────────────────┬───────────────────────────────────────┘
                           │ assigns lane / advances state
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│  Worker layer (Hermes) — seven profiles execute in their lanes   │
│  Librarian · Mapper · Socratic · Writer · Verifier · Coder       |
|  · Linter                                                        │
└──────────────────────────┬───────────────────────────────────────┘
                           │ every write checked by the policy MCP
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│  Vault layer (Obsidian) — durable knowledge by lifecycle stage   │
│  00-meta · 10-inbox · 20-sources · 30-synthesis                  │
│  40-workbench · 50-deliverables · 90-assets · 95-archive         │
└──────────────────────────────────────────────────────────────────┘
```

## Documents in this section

| Page                                      | What it covers                                                                                                                  |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| [The vault](vault.md)                     | The vault as a knowledge structure: lifecycle folders, review-gated zones, special root files, and the promotion path in prose. |
| [The memory model](memory-model.md)       | The seven memory substrates — their scope, owner, and lifespan — and why configuration is not memory.                           |
| [The control plane](control-plane.md)     | How a human request reaches Hermes: the thin UI → API → MCP → worker chain, and why it is fail-closed and per-profile.          |
| [Interaction channels](human-channels.md) | The interaction surfaces — Obsidian, CLI, Telegram, and the programs-only API server — and the one-mode-per-channel principle.  |
| [Session logging](session-logging.md)     | What each agent session records, why per-session summaries and the audit log are kept separate, and why one file per session.   |

## Where to go next

- **Why the design is shaped this way** (`why-*` arguments, including [Why three layers, not one](../rationale/why-three-layers.md)) → [Design rationale](../rationale/README.md)
- **The board state machine** the profiles execute against → [Kanban board](../kanban-board/README.md)
- **How profiles and the vault are packaged and installed** → [Deployment](../deployment/README.md)
- **Operational reference** (permission matrices, command lists, config formats) → [Reference](../../reference)
