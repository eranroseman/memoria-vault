---
title: Profiles
parent: Explanation
nav_order: 4
has_children: true
permalink: /explanation/profiles/
---

# Profiles

Memoria runs **one conversational agent — the Co-PI — and four background agents** it delegates to ([ADR-48](../../adr/48-copi-and-agent-consolidation.md)). The PI talks to exactly one agent; everything else runs as a lane (a background worker on the board — see [Glossary](../../reference/glossary.md)) on the board (the kanban board), invisible until it has something for you. A profile's stable trait is its **posture** — a stance like *faithful* or *skeptical* — while the skills it runs attach per lane.

## The one you talk to

| Agent | Posture | Where | What it does |
| --- | --- | --- | --- |
| **[The Co-PI](co-pi.md)** | reflective thinking-partner | the Agent Client pane | Holds the conversation, asks the sharpening questions, and delegates every write as a task card (a unit of work on the board — see [Glossary](../../reference/glossary.md)). Read-only by design. |

## The four background lanes

| Agent | Posture | Lane(s) | What it does |
| --- | --- | --- | --- |
| **[The Librarian](librarian.md)** | faithful | catalog · extract · link · map | The four processing tasks — intake, distillation, connection, and corpus mapping. Proposes generously; the review gate (the human approval step — see [Glossary](../../reference/glossary.md)) filters. |
| **[The Writer](writer.md)** | generative, draft-only | draft | Composes prose and outlines into project scratch. Never canonizes, never self-verifies. |
| **[The Peer-reviewer](peer-reviewer.md)** | skeptical, independent | verify | The formal review gate: judgment checks and the conceptual red-team. Flags, never fixes. |
| **[The Engineer](engineer.md)** | delegating | code | Scaffolds the handoff to an external coding agent and owns the commit gate. Writes no code itself. |

All five profiles ship; the Writer, Peer-reviewer, and Engineer run as background lanes, and the Project space (a navigation surface and dashboard-as-note — see [Glossary](../../reference/glossary.md)) those lanes write around — project folders, active theses, and structural-impact cache — ships alongside them. Deterministic work — ingest, search, clustering, the project structural-impact operation, verification sweeps, and the Linter — is [Operations](../operations/README.md), not agents: no posture, no board lane.

The tables above orient by posture; the canonical lane→profile map, write-scope ceilings, and bundled-skills counts live in [Profile capabilities](../../reference/profiles.md).

## Shared layer, unique layer

Each agent is a **shared** layer (the vault's `AGENTS.md` house rules, one copy for all) plus a **unique** layer (its own posture, skills, model, and connections). How those layers are packaged and shipped is owned by [Distribution model](../deployment/distribution-model.md); what matters here is the consequence — the agents share the house rules but each brings its own stance and toolset.

The Co-PI is the sole memory carrier while the background lanes stay stateless propose-then-dispose executors (they suggest; only the PI decides) — the substrate split behind that is [The memory model](../architecture/memory-model.md). Two affordances are Co-PI-only — the Hermes self-improving loop and `/personality` tuning ([The Co-PI](co-pi.md)) — and the specialists' postures are fixed by design, stable traits rather than per-run knobs.

## The bounded rule

All five agents **propose**; the **PI disposes** — promotions, the `retracted` decision, and gated-zone writes are PI-only, enforced by the policy MCP. Why that gate is structural rather than a convention is [Why the review gate is structural](../rationale/why-human-gate.md); how far each agent may hand support work onward is its [Delegation posture](delegation-posture.md).

## Where to go next

- Why one Co-PI + four background lanes: [Why specialist profiles, not a generalist agent](../rationale/why-specialist-profiles.md)
- The deterministic actors that left the profile set: [Operations](../operations/README.md)
- How cards reach the lanes and come back: [The control plane](../architecture/control-plane.md)
