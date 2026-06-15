---
title: Explanation
nav_order: 5
has_children: true
permalink: /explanation/
---

# Explanation

This section is for **understanding** Memoria — what it is, how it thinks, and why it was built the way it was. These documents answer "why" and "what is" questions. They are for reading and reflection, not for following step-by-step.

If you need to *do* something, see [how-to guides](../how-to-guides). If you need exact values, field names, or configuration formats, see [Reference](../reference). If you want a guided first experience, see [Tutorials](../tutorials).

---

## What explanation documents do (and don't do)

Explanation documents build a mental model. They:

- Answer "why is it this way?" and "what does this mean?"
- Compare alternatives and explain trade-offs
- Provide context and intellectual background
- Make connections between concepts

They don't include step-by-step instructions, lookup tables, or precise configuration values. When an explanation references exact schemas or commands, it points to the reference section.

---

## Conceptual map

Read from the inside out: start with what the system is, then why it's shaped that way, then how each design area works.

### Start here — [Overview](overview/README.md)

1. **[What Memoria is](overview/what-memoria-is.md)** — the system's identity: what it is, what it's not, and why it exists. Everything else builds on this.
2. **[Intellectual foundations](overview/intellectual-foundations.md)** — the three ideas Memoria is built on (Karpathy, Zettelkasten, Memex) and how the AI-research systems survey shaped the design.
3. **[Design principles](overview/design-principles.md)** — the cross-cutting principles the design returns to.

### Why the design is shaped this way

1. **[Why the architecture is layered](rationale/why-three-layers.md)** — why board, workers, and vault are kept separate.
2. **[Why specialist profiles, not a generalist agent](rationale/why-specialist-profiles.md)** — why five profiles (one conversational Co-PI plus four background lanes) instead of one generalist agent.
3. **[Why the review gate is structural](rationale/why-human-gate.md)** — why the review gate is structural, not advisory.
4. **[Why Memoria doesn't pursue full autonomy](rationale/why-not-autonomous.md)** — the autonomy ceiling and why Memoria doesn't cross it.

### How it's structured

1. **[Architecture](architecture/README.md)** — the seven-layer model and the structural pages (control plane, memory tiers, channels, vault, logging).
2. **[Knowledge](knowledge/README.md)** — how the vault organizes durable knowledge (lifecycle folders, note types, gated promotion).
3. **[Workflows](workflows/README.md)** — how work moves through the system (the board as a state machine, review as a state).

---

## Entry points by background

**New to Memoria:** The two identity documents, then [Why the architecture is layered](rationale/why-three-layers.md), the [knowledge model overview](knowledge/README.md), and the [workflow overview](workflows/README.md) together give a working mental model. The architecture, knowledge, and workflow sections fill in the detail.

**Coming from another agent system (LangChain, CrewAI, autogen, etc.):** The key differences — specialist lanes, structural human gate, no reasoning orchestrator — are concentrated in [Why specialist profiles, not a generalist agent](rationale/why-specialist-profiles.md), [Why the review gate is structural](rationale/why-human-gate.md), and [The board as a state machine (the control plane)](workflows/board-as-state-machine.md).

---

## All sections

The curated path above is a reading order, not a full index. The sidebar lists every page; the sections are:

- [Overview](overview/README.md) — start here: what-memoria-is, intellectual-foundations, design-principles
- [Design rationale](rationale/README.md) — the `why-*` arguments: three-layers, specialist-profiles, human-gate, not-autonomous, hermes, computational-methods, pattern-provenance
- [Architecture](architecture/README.md) — what each layer and surface *is*: vault, the memory model, control-plane, interaction channels, session-logging
- [Knowledge](knowledge/README.md) — how durable knowledge is organized: note-types, knowledge-cycle, note-body-structure, lifecycle-over-topic, promotion-model, vocabulary-discipline, common-pitfalls
- [Profiles](profiles/README.md) — the five profiles: Co-PI (conversational front) plus four background lanes — librarian, writer, peer-reviewer, engineer — plus delegation-posture
- [Kanban board](kanban-board/README.md) — the board as coordination layer: states, card-schema, obsidian-projection
- [Workflows](workflows/README.md) — how work moves: compile-and-compose, board-as-state-machine, review-as-state, plus verify-on-commit
- [Obsidian](obsidian/README.md) — how the human interacts through Obsidian: home, the-status-line, callouts, agent-client-picker, visual-discipline, design-system
- [Dashboards](dashboards/README.md) — the twelve dashboards, grouped: daily-glance, synthesis-agenda, structural-health, operational-health
- [Deployment](deployment/README.md) — how the system is packaged and installed: distribution-model, bootstrap-installer, deployment-options

---

## For decisions and direction

The *why* behind a specific choice lives in an ADR — see [Decisions](../adr); deferred and forward-looking decisions are ADRs too (`status: deferred`). The release plan lives in the repo's [Releasing](https://github.com/eranroseman/memoria-vault/tree/main/docs/releasing) docs.
