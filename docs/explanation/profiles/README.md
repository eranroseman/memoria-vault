---
title: Profiles
parent: Explanation
nav_order: 4
has_children: true
permalink: /explanation/profiles/
---

# Profiles

Memoria runs **one conversational agent — the Co-PI — and four background agents** it delegates to ([ADR-48](../../adr/48-copi-and-agent-consolidation.md)). The PI talks to exactly one agent; everything else runs as a lane on the board, invisible until it has something for you. A profile's stable trait is its **posture** — a stance like *faithful* or *skeptical* — while the skills it runs attach per lane.

## The one you talk to

| Agent | Posture | Where | What it does |
| --- | --- | --- | --- |
| **[The Co-PI](co-pi.md)** | reflective thinking-partner | the ACP pane (the desk) | Holds the conversation, asks the sharpening questions, and delegates every write as a task card. Read-only by design. |

## The four background lanes

| Agent | Posture | Lane(s) | What it does |
| --- | --- | --- | --- |
| **[The Librarian](librarian.md)** | faithful | catalog · extract · link · map | The four processing tasks — intake, distillation, connection, and corpus mapping. Proposes generously; the gate filters. |
| **[The Writer](writer.md)** | generative, draft-only | draft | Composes prose and outlines into project scratch. Never canonizes, never self-verifies. |
| **[The Peer-reviewer](peer-reviewer.md)** | skeptical, independent | verify | The formal review gate: judgment checks and the conceptual red-team. Flags, never fixes. |
| **[The Engineer](engineer.md)** | delegating | code | Scaffolds the handoff to an external coding agent and owns the commit gate. Writes no code itself. |

**v0.1.0-alpha.2 shipped all five profiles**; the Writer, Peer-reviewer, and Engineer run as background lanes. alpha.5 adds the Project gate surface those lanes write around: project folders, active theses, and structural-impact cache. Deterministic work — ingest, search, clustering, the Project gate operation, verification sweeps, and the Linter — is [Operations](../operations/README.md), not agents: no posture, no board lane.

The tables above orient by posture; the canonical lane→profile map, write-scope ceilings, and bundled-skills counts live in [Profile capabilities](../../reference/profiles.md).

## Shared layer, unique layer

Each agent is a **shared** layer (the vault's `AGENTS.md` house rules, one copy for all) plus a **unique** layer (its own posture, skills, model, and connections). How those layers are packaged and shipped is owned by [Distribution model](../deployment/distribution-model.md); what matters here is the consequence — the agents share the house rules but each brings its own stance and toolset.

The Co-PI is the sole memory carrier, and two affordances are Co-PI-only — the Hermes self-improving loop and `/personality` tuning ([The Co-PI](co-pi.md)). The specialists' postures are fixed by design — stable traits, not per-run knobs — and the lanes stay stateless propose-then-dispose executors.

## The bounded rule

All five agents **propose**; the **PI disposes**. Promotions, the `retracted` decision, and gated-zone writes are PI-only, enforced by the policy MCP. How far each agent may hand support work onward is its [Delegation posture](delegation-posture.md).

## Where to go next

- Why one Co-PI + four lanes, not seven specialists: [Why specialist profiles, not a generalist agent](../rationale/why-specialist-profiles.md)
- The deterministic actors that left the profile set: [Operations](../operations/README.md)
- How cards reach the lanes and come back: [The control plane](../architecture/control-plane.md)
