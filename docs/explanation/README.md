---
title: Explanation
nav_order: 5
has_children: true
permalink: /explanation/
---

# Explanation

This section is Memoria's operational overview: architecture, knowledge,
execution, surfaces, deployment, and design rationale.
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
history, see [Design rationale](rationale/README.md).

## Reading map

1. **[Architecture](architecture/README.md)** — the seven-layer model and the structural pages.
2. **[Knowledge](knowledge/README.md)** — how the vault organizes durable knowledge.
3. **[Execution](execution/README.md)** — operations, operation postures, requests, attention, and review state.
4. **[Surfaces](surfaces/README.md)** — dashboards and optional editor integration boundaries.
5. **[Deployment](deployment/README.md)** — how Memoria is packaged and installed.
6. **[Design rationale](rationale/README.md)** — why Memoria keeps these boundaries.

---

## Entry points by background

**New to Memoria:** Read [Home](../README.md), then
[Architecture](architecture/README.md), [Knowledge](knowledge/README.md), and
[Request control plane](execution/control-plane/README.md). Design rationale
explains why those choices were made.

**Coming from another agent system:** The key differences are checked request
rows, operation ceilings, a structural human gate, and no reasoning orchestrator.
Start with [Operation postures](execution/operation-postures/README.md), [Request control plane](execution/control-plane/README.md),
then the design pages on [Why operation postures](rationale/boundaries/why-operation-postures.md)
and [the review gate](rationale/boundaries/why-review-gate-is-structural.md).

## For decisions and direction

The maintained arguments live in [Design rationale](rationale/README.md). Dated
decisions live in [design history](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md);
forward-looking decisions live in the active release decision ledger until they
are accepted, rejected, or closed into design history. Scheduling and readiness
live on GitHub issues and milestones. Release procedure lives in
`.agents/playbooks/release.md`.
