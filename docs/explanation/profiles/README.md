---
title: Profiles
parent: Explanation
nav_order: 4
has_children: true
permalink: /explanation/profiles/
---

# Profiles

Memoria runs **one conversational agent — the Co-PI — and four background agents** it delegates to ([ADR-48](../../adr/48-copi-and-agent-consolidation.md)). The PI talks to exactly one agent; everything else runs as a lane (a background worker on the board — see [Glossary](../../reference/glossary.md)) on the board (the kanban board), invisible until it has something for you. A profile's stable trait is its **posture** — a stance like *faithful* or *skeptical* — while the skills it runs attach per lane.

For the shared PI, Co-PI, lanes, board, and vault terms, see [Home](../../README.md).

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

## Where to go next

- Why one Co-PI + four background lanes: [Why specialist profiles, not a generalist agent](../../design/why-specialist-profiles.md)
- Why the profile boundaries are strict: [Why profile boundaries exist](../../design/why-profile-boundaries.md)
- The deterministic actors that left the profile set: [Operations](../operations/README.md)
- How cards reach the lanes and come back: [The control plane](../architecture/control-plane.md)
