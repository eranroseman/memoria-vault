---
title: Explanation
nav_order: 14
has_children: true
permalink: /explanation/
---

# Explanation

This section is Memoria's operational overview: architecture, knowledge,
operation postures, operations, dashboards, deployment, and optional editor
surfaces.
It explains how the system is shaped so you can use and evaluate it without
reading the full design argument.

Memoria is a vault-first research system. The vault holds durable knowledge, the
SQLite engine holds request and graph state, the CLI is the required product
surface, and the Inbox shows the decisions that need attention now. Optional
adapters may present chat, board, or editor views, but they do not replace the
CLI/engine authority.

Start with [Home](../README.md) if the basic vocabulary is unfamiliar. If you
need to *do* something, see [How-to guides](../how-to-guides/). If you need exact
values, field names, runtime contracts, or configuration formats, see
[Reference](../reference/). If you want the maintained rationale and decision
history, see [Design](../design/README.md).

## Reading map

1. **[Architecture](architecture/README.md)** — the seven-layer model and the structural pages.
2. **[Knowledge](knowledge/README.md)** — how the vault organizes durable knowledge.
3. **[Operation postures](operation-postures/README.md)** — how old profile language maps to standalone requests and operations.
4. **[Operations](operations.md)** — the deterministic layer below the agents.
5. **[Request control plane](control-plane/README.md)** — request state, attention, and the old board boundary.
6. **[Obsidian](obsidian/README.md)** — optional editor integration boundaries.
7. **[Surfaces and dashboards](dashboards/README.md)** — how health, queues, and maintenance surface.
8. **[Deployment](deployment.md)** — how Memoria is packaged and installed.

---

## Entry points by background

**New to Memoria:** Read [Home](../README.md), then
[Architecture](architecture/README.md), [Knowledge](knowledge/README.md), and
[Request control plane](control-plane/README.md). Design explains why those choices
were made.

**Coming from another agent system:** The key differences are checked request
rows, operation ceilings, a structural human gate, and no reasoning orchestrator.
Start with [Operation postures](operation-postures/README.md), [Request control plane](control-plane/README.md),
then the design pages on [operation postures](../design/why-specialist-postures.md)
and [the review gate](../design/why-review-gate-is-structural.md).

## For decisions and direction

The maintained arguments live in [Design](../design/README.md). Dated
decisions live in [design history](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md);
forward-looking decisions live in the active release decision ledger until they
are accepted, rejected, or closed into design history. Scheduling and readiness
live on GitHub issues and milestones. Release procedure lives in
`.agents/playbooks/release.md`.
