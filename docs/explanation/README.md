---
title: Explanation
nav_order: 4
has_children: true
permalink: /explanation/
---

# Explanation

This section is for **understanding** Memoria — what it is, how it thinks, and why it was built the way it was. These documents answer "why" and "what is" questions. They are for reading and reflection, not for following step-by-step.

If you need to *do* something, see [how-to guides](../how-to-guides/). If you need exact values, field names, or configuration formats, see [reference](../reference/). If you want a guided first experience, see [tutorials](../tutorials/).

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

### Start here

1. **[what-memoria-is.md](what-memoria-is.md)** — the system's identity: what it is, what it's not, and why it exists. Everything else builds on this.
2. **[intellectual-foundations.md](intellectual-foundations.md)** — the three ideas Memoria is built on (Karpathy, Zettelkasten, Memex) and how the AI-research systems survey shaped the design.

### Why the design is shaped this way

1. **[rationale/why-three-layers.md](rationale/why-three-layers.md)** — why board, workers, and vault are kept separate.
2. **[rationale/why-specialist-profiles.md](rationale/why-specialist-profiles.md)** — why seven specialists instead of one generalist agent.
3. **[rationale/why-human-gate.md](rationale/why-human-gate.md)** — why the review gate is structural, not advisory.
4. **[rationale/why-not-autonomous.md](rationale/why-not-autonomous.md)** — the autonomy ceiling and why Memoria doesn't cross it.

### How it's structured

1. **[architecture/README.md](architecture/README.md)** — the three-layer model and the structural pages (control plane, memory tiers, channels, vault, logging).
2. **[knowledge/README.md](knowledge/README.md)** — how the vault organizes durable knowledge (lifecycle folders, note types, gated promotion).
3. **[workflows/README.md](workflows/README.md)** — how work moves through the system (the board as a state machine, review as a state).

---

## Entry points by background

**New to Memoria:** The two identity documents, then [why-three-layers](rationale/why-three-layers.md), the [knowledge model overview](knowledge/README.md), and the [workflow overview](workflows/README.md) together give a working mental model. The architecture, knowledge, and workflow sections fill in the detail.

**Coming from another agent system (LangChain, CrewAI, autogen, etc.):** The key differences — specialist lanes, structural human gate, no reasoning orchestrator — are concentrated in [why-specialist-profiles](rationale/why-specialist-profiles.md), [why-human-gate](rationale/why-human-gate.md), and [board-as-state-machine](workflows/board-as-state-machine.md).

---

## All sections

The curated path above is a reading order, not a full index. The sidebar lists every page; the sections are:

**Top-level pages**

- [what-memoria-is.md](what-memoria-is.md) · [intellectual-foundations.md](intellectual-foundations.md) — the entry points (start here)
- [design-principles.md](design-principles.md) — the cross-cutting principles the design returns to

**Sections** (each has its own README)

- [Design rationale](rationale/README.md) — the `why-*` arguments: three-layers, specialist-profiles, human-gate, not-autonomous, hermes, computational-methods, pattern-provenance
- [Architecture](architecture/README.md) — what each layer and surface *is*: control-plane, memory-tiers, interaction channels, vault, session-logging
- [Knowledge](knowledge/README.md) — how durable knowledge is organized: lifecycle-over-topic, note-types, promotion-model, knowledge-cycle, note-body-structure, vocabulary-discipline, common-pitfalls
- [Workflows](workflows/README.md) — how work moves: board-as-state-machine, review-as-state, verify-on-commit
- [Kanban board](kanban-board/README.md) — the board as coordination layer: card-schema, states
- [Deployment](deployment/README.md) — how the system is packaged and installed: distribution-model, bootstrap-installer
- [Profiles](profiles/README.md) — the seven specialist profiles: librarian, mapper, socratic, writer, verifier, coder, linter
- [Dashboards](dashboards/README.md) — the ten dashboards, grouped: daily-glance, synthesis-agenda, structural-health, operational-health
- [Obsidian](obsidian/README.md) — how the human interacts through Obsidian: home, visual-discipline, design-system, the-status-line, callouts, agent-client-picker

---

## For decisions and direction

The *why* behind a specific choice lives in an ADR. The forward plan lives in the timeline. Both are in [project-files/](../../project-files/): [decisions/](../../project-files/decisions/) for the ADRs, [operations/](../../project-files/operations/) for direction and timeline.
