---
title: Explanation
nav_order: 14
has_children: true
permalink: /explanation/
---

# Explanation

This section is Memoria's operational overview: architecture, knowledge, profiles,
operations, board coordination, dashboards, deployment, and the Obsidian surface.
It explains how the system is shaped so you can use and evaluate it without
reading the full design argument.

Memoria is a vault-first research system. The vault holds durable knowledge, the
board holds transient work, Hermes runs the specialist profiles that propose
changes back to the human, and the Inbox shows the decisions that need attention
now.

Start with [Home](../README.md) if the basic vocabulary is unfamiliar. If you
need to *do* something, see [How-to guides](../how-to-guides). If you need exact
values, field names, runtime contracts, or configuration formats, see
[Reference](../reference). If you want the maintained rationale and decision
history, see [Developers](../developers.md).

## Reading map

1. **[Architecture](architecture/README.md)** — the seven-layer model and the structural pages.
2. **[Knowledge](knowledge/README.md)** — how the vault organizes durable knowledge.
3. **[Profiles](profiles/README.md)** — the Co-PI and specialist background profiles.
4. **[Operations](operations.md)** — the deterministic layer below the agents.
5. **[Kanban board](kanban-board/README.md)** — the board as the coordination layer.
6. **[Obsidian](obsidian/README.md)** — how the human works in the vault.
7. **[Surfaces and dashboards](dashboards/README.md)** — how health, queues, and maintenance surface.
8. **[Deployment](deployment.md)** — how Memoria is packaged and installed.

---

## Entry points by background

**New to Memoria:** Read [Home](../README.md), then
[Architecture](architecture/README.md), [Knowledge](knowledge/README.md), and
[Kanban board](kanban-board/README.md). The Design Book explains why those choices
were made.

**Coming from another agent system:** The key differences are specialist lanes,
a structural human gate, and no reasoning orchestrator. Start with
[Profiles](profiles/README.md), [Kanban board](kanban-board/README.md),
then the Design Book pages on [specialist profiles](../design/why-specialist-profiles.md)
and [the review gate](../design/why-review-gate-is-structural.md).

## For decisions and direction

The maintained arguments live in the [Design Book](../design/README.md). Dated
decisions live in [Decision records](../adr); forward-looking decisions are ADRs
too (`status: proposed`) until accepted or rejected. Scheduling and readiness live
on GitHub issues and milestones. Release procedure lives in
`.agents/playbooks/release.md`.
