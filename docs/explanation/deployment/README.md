---
title: Deployment
parent: Explanation
nav_order: 7
has_children: true
permalink: /explanation/deployment/
---

# Deployment

How Memoria is packaged, installed, and deployed. These pages explain the *rationale* behind the distribution model and the installer — for the operational steps see the [setup how-to guides](../../how-to-guides/setup/), and for exact inventories see [reference/installer.md](../../reference/installer.md).

| Page | What it explains |
|---|---|
| [Distribution model](distribution-model.md) | How profiles and the vault are packaged and installed — the repo as the install unit, idempotent deploy, hand-authored profiles |
| [Bootstrap installer](bootstrap-installer.md) | The one-command installer's design and decided rules (WSL2/Linux, one bash implementation, inspect-first) |
| [Deployment options](deployment-options.md) | The adopted `local-only` default and the conventions common to every sync pattern (Git history, `memoria.bib` in-vault, per-session logs, one dispatcher per vault) |

---

## Related

- The steps to actually install: [Setup how-to guides](../../how-to-guides/setup/)
- Installer inventories (what gets copied where): [reference/installer.md](../../reference/installer.md)
- The repo-as-install-unit decision: [ADR-26](../../../project-files/decisions/26-repo-as-install-unit.md)
