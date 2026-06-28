---
title: Profiles
parent: Explanation
nav_order: 4
has_children: true
permalink: /explanation/profiles/
---

# Profiles

Memoria runs **one conversational agent — the Co-PI — and four background agents** it delegates to ([ADR-48](../../adr/48-copi-and-agent-consolidation.md)). The PI talks to the Co-PI; background agents run as board lanes and surface only when they need attention. A profile's stable trait is its **posture** — a stance like *faithful* or *skeptical* — while skills attach per lane.

For the shared PI, Co-PI, lanes, board, and vault terms, see [Home](../../README.md).

## The one you talk to

| Agent | Posture | Where | What it does |
| --- | --- | --- | --- |
| **[The Co-PI](co-pi.md)** | reflective thinking-partner | the Agent Client pane | Holds the conversation, asks the sharpening questions, and delegates every write as a task card. Read-only by design. |

## The four background lanes

| Agent | Posture | Lane(s) | What it does |
| --- | --- | --- | --- |
| **[The Librarian](librarian.md)** | faithful | catalog · extract · link · map | Intake, distillation, connection, and corpus mapping. Proposes generously; the review gate filters. |
| **[The Writer](writer.md)** | generative, draft-only | draft | Composes prose and outlines into project scratch. Never canonizes, never self-verifies. |
| **[The Peer-reviewer](peer-reviewer.md)** | skeptical, independent | verify | The formal review gate: judgment checks and the conceptual red-team. Flags, never fixes. |
| **[The Engineer](engineer.md)** | delegating | code | Scaffolds the handoff to an external coding agent and owns the commit/revert checkpoint. Writes no code itself. |

All five profiles ship. Deterministic work — ingest, search, clustering, project structural impact, verification sweeps, and the Linter — is [Operations](../operations/README.md), not agents: no posture, no board lane.

The tables above orient by posture; the canonical lane→profile map, write-scope ceilings, and bundled-skills counts live in [Profile capabilities](../../reference/profiles.md).

## Delegation posture

Agents may hand off narrow support work, never their defining judgment. Strongest
delegators first:

| Profile | Delegation posture |
| --- | --- |
| Engineer | Widest: substantive coding goes to the external agent by design; commits stay per task. |
| Writer | Supportive: facts and cleanup; synthesis stays local. |
| Librarian | Targeted: narrow enrichment and source lookups; discovery ownership stays local. |
| Peer-reviewer | Very low: delegation weakens independence; it runs its own traces. |
| Co-PI | None as a helper-spawn model: every write leaves as a routed board card under another lane's ceiling. |

Whatever a helper or external agent produces re-enters as a proposal under the
originating lane's write ceiling, and the PI disposes.

## Where to go next

- Why one Co-PI + four background lanes: [Why specialist profiles, not a generalist agent](../../design/why-specialist-profiles.md)
- Why the profile boundaries are strict: [Why specialist profiles, not a generalist agent](../../design/why-specialist-profiles.md)
- The deterministic actors that left the profile set: [Operations](../operations/README.md)
- How cards reach the lanes and come back: [The Kanban board](../kanban-board/README.md)
