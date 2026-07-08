---
title: Deployment
parent: Explanation
nav_order: 5
permalink: /explanation/deployment/
---

# Deployment

How Memoria is packaged, installed, and deployed. The supported operating model is
**local-only**: one workstation owns the workspace and standalone CLI/engine. Git
provides history and recovery; it is not treated as a live sync bus.

For operational steps see the [setup how-to guides](../../how-to-guides/setup/README.md),
for exact inventories see [Installer (bootstrap)](../../reference/installer.md),
and for maintained rationale see the design links below.

## Current operating model

The current model is deliberately local: the workspace, runtime state, generated
projections, and provider configuration all belong to one machine. Git records
history; it does not coordinate live writers. Operator-managed scheduled tasks
may call the same engine, but they do not create a second authority.

Multi-machine patterns are not the current operating model. A future second-device
or always-on topology needs a new deployment decision before support.

Any future sync pattern keeps the same boundaries: the vault is the knowledge
store, runtime state remains workspace-local unless explicitly promoted, and only
one engine instance writes task state for a workspace at a time.

---

## Where to go next

- To install: [Setup how-to guides](../../how-to-guides/setup/README.md)
- To inspect what the installer copies: [Installer (bootstrap)](../../reference/installer.md)
- To understand why the repo ships this way: [Distribution model](../../design/deployment/distribution-model.md)
- To understand why bootstrap is narrow: [Bootstrap installer](../../design/deployment/bootstrap-installer.md)
- To track future sync or always-on work: [Always-on VPS design](../../design/deployment/always-on-vps-design.md)
