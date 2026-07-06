---
title: Deployment
parent: Explanation
nav_order: 8
permalink: /explanation/deployment/
---

# Deployment

How Memoria is packaged, installed, and deployed. The supported operating model is
**local-only**: one workstation owns the workspace and standalone CLI/engine. Git
provides history and recovery; it is not treated as a live sync bus.

For operational steps see the [setup how-to guides](../how-to-guides/setup/README.md),
for exact inventories see [Installer (bootstrap)](../reference/installer.md),
and for maintained rationale see the Design Book links below.

## Current operating model

| Piece | Current posture |
| --- | --- |
| Workspace | Local folder populated from `vault-template/` by the installer. |
| Runtime | Standalone `memoria` CLI/engine plus workspace-local `.memoria/memoria.sqlite`. |
| Bibliography | Memoria generates tracked `bibliography.bib` from checked SQLite catalog rows. |
| Dispatch | CLI commands, file-change observers, and operator-managed scheduled tasks call the same engine. |
| Secrets | Per-machine environment/provider config, never committed or synced. |

Multi-machine patterns are not the current operating model. A future second-device
or always-on topology needs a new deployment decision before support.

Any future sync pattern keeps the same boundaries: the vault is the knowledge
store, runtime state remains workspace-local unless explicitly promoted, and only
one engine instance writes task state for a workspace at a time.

---

## Related

- The steps to actually install: [Setup how-to guides](../how-to-guides/setup/README.md)
- Installer inventories (what gets copied where): [Installer (bootstrap)](../reference/installer.md)
- Distribution rationale: [Distribution model](../design/distribution-model.md)
- Installer rationale: [Bootstrap installer](../design/bootstrap-installer.md)
- The repo-as-install-unit decision: [standalone engine with operations as product code, no agent tools](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)
