---
title: Deployment
parent: Explanation
nav_order: 9
has_children: true
permalink: /explanation/deployment/
---

# Deployment

How Memoria is packaged, installed, and deployed. These pages explain the _rationale_ behind the distribution model and the installer — for the operational steps see the [setup how-to guides](../../how-to-guides/setup), and for exact inventories see [Installer (bootstrap)](../../reference/installer.md).

| Page                                          | What it explains                                                                                                                                                    |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Bootstrap installer](bootstrap-installer.md) | The one-command installer's design and decided rules for native Windows production and Linux/WSL testing                                                           |
| [Deployment options](deployment-options.md)   | The adopted `local-only` default and the conventions common to every sync pattern (Git history, `memoria.bib` in-vault, the append-only audit log, one dispatcher per vault) |

---

## Related

- The steps to actually install: [Setup how-to guides](../../how-to-guides/setup)
- Installer inventories (what gets copied where): [Installer (bootstrap)](../../reference/installer.md)
- Distribution rationale: [Distribution model](../../design/distribution-model.md)
- The repo-as-install-unit decision: [ADR-26](../../adr/26-repo-as-install-unit.md)
