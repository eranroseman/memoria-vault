---
title: Deployment
parent: Explanation
nav_order: 9
permalink: /explanation/deployment/
---

# Deployment

How Memoria is packaged, installed, and deployed. The supported operating model is
**local-only**: one workstation owns the vault and the Hermes dispatcher. Git
provides history and recovery; it is not treated as a live sync bus.

For operational steps see the [setup how-to guides](../../how-to-guides/setup),
for exact inventories see [Installer (bootstrap)](../../reference/installer.md),
and for maintained rationale see the Design Book links below.

## Current operating model

| Piece | Current posture |
| --- | --- |
| Vault | Local Obsidian folder populated from `src/` by the installer. |
| Runtime | Hermes profiles on the same host as the production vault. |
| Bibliography | Better BibTeX exports `memoria.bib` inside the vault. |
| Dispatch | One Hermes dispatcher per vault. |
| Secrets | Per-machine `.env` files, never committed or synced. |

The multi-machine patterns (`local-mesh`, `obsidian-sync`, and `always-on`) are
not the current operating model. They are captured as future/deferred topology in
[ADR-63](../../adr/63-multi-machine-deployment.md).

Any future sync pattern keeps the same boundaries: the vault is the knowledge
store, Hermes state remains machine-local unless explicitly promoted, and only one
dispatcher writes task state for a vault at a time.

---

## Related

- The steps to actually install: [Setup how-to guides](../../how-to-guides/setup)
- Installer inventories (what gets copied where): [Installer (bootstrap)](../../reference/installer.md)
- Distribution rationale: [Distribution model](../../design/distribution-model.md)
- Installer rationale: [Bootstrap installer](../../design/bootstrap-installer.md)
- Deferred multi-machine design: [ADR-63](../../adr/63-multi-machine-deployment.md)
- The repo-as-install-unit decision: [ADR-26](../../adr/26-repo-as-install-unit.md)
