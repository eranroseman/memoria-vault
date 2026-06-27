---
title: Explanation
nav_order: 14
has_children: true
permalink: /explanation/
---

# Explanation

This section is for Memoria's operational explanations: architecture, knowledge,
profiles, workflows, dashboards, deployment, and the Obsidian surface. It explains
how the system is shaped so you can use and evaluate it without reading the full
design argument.

Start with [The model](../the-model.md) if the basic vocabulary is unfamiliar. If you
need to *do* something, see [How-to guides](../how-to-guides). If you need exact
values, field names, runtime contracts, or configuration formats, see
[Reference](../reference). If you want the maintained rationale and decision
history, see [Developers](../developers.md).

---

## What explanation pages do

Explanation pages build a working mental model. They:

- Explain what each part of Memoria is for
- Connect the pieces without turning into a reference table
- Point to the Design Book or ADRs when the rationale matters

They do not carry step-by-step procedures, lookup tables, or full design essays.
When a page needs exact schemas or commands, it points to Reference. When it needs
the deeper argument, it points to the Design Book or ADRs.

---

## Reading map

1. **[Architecture](architecture/README.md)** — the seven-layer model and the structural pages.
2. **[Knowledge](knowledge/README.md)** — how the vault organizes durable knowledge.
3. **[Profiles](profiles/README.md)** — the Co-PI and the four background lanes.
4. **[Kanban board](kanban-board/README.md)** — the board as the coordination layer.
5. **[Workflows](workflows/README.md)** — how work moves through the system.
6. **[Obsidian](obsidian/README.md)** — how the human works in the vault.
7. **[Dashboards](dashboards/README.md)** — how health, queues, and maintenance surface.
8. **[Deployment](deployment/README.md)** — how Memoria is packaged and installed.
9. **[Operations](operations/README.md)** — the deterministic layer below the agents.

---

## Entry points by background

**New to Memoria:** Read [The model](../the-model.md), then
[Architecture](architecture/README.md), [Knowledge](knowledge/README.md), and
[Workflows](workflows/README.md). The Design Book explains why those choices were
made.

**Coming from another agent system:** The key differences are specialist lanes,
a structural human gate, and no reasoning orchestrator. Start with
[Profiles](profiles/README.md), [The board as a state machine](workflows/board-as-state-machine.md),
then the Design Book pages on [specialist profiles](../design/why-specialist-profiles.md)
and [the review gate](../design/why-human-gate.md).

---

## All sections

The curated path above is a reading order, not a full index. The sidebar lists
every page; the sections are:

- [Architecture](architecture/README.md) — what each layer and surface is
- [Knowledge](knowledge/README.md) — how durable knowledge is organized
- [Profiles](profiles/README.md) — the five profiles and their delegation posture
- [Kanban board](kanban-board/README.md) — board states, card schema, and Obsidian projection
- [Workflows](workflows/README.md) — how work moves
- [Obsidian](obsidian/README.md) — home, callouts, Agent Client pane, and design system
- [Dashboards](dashboards/README.md) — daily glance, synthesis agenda, structural health, and operational health
- [Deployment](deployment/README.md) — bootstrap installer and deployment options
- [Operations](operations/README.md) — deterministic operations below the agents

---

## For decisions and direction

The maintained arguments live in the [Design Book](../design/README.md). Dated
decisions live in [Decision records](../adr); forward-looking decisions are ADRs
too (`status: proposed`) until accepted or rejected. Scheduling and readiness live
on GitHub issues. The release plan lives in the repo's
[Releasing](https://github.com/eranroseman/memoria-vault/tree/main/docs/releasing)
docs.
