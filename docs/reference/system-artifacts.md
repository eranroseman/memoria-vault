---
title: System artifacts
parent: System and infrastructure
grand_parent: Reference
---

# System artifacts

Visible system artifacts live under `system/` in the runtime vault. They are not hidden `.memoria/` internals; the PI can inspect them from Obsidian.

| Runtime path | What it is | Reference |
| --- | --- | --- |
| `system/vocabulary.md` | Controlled vocabulary for `research_area`, `methodology`, and claim `topics`. | [Vocabulary](vocabulary.md) |
| `system/eval/` | Gold-task fixtures for vault-eval dispatch and scoring. | [Vault eval](vault-eval.md) |
| `system/dashboards/*.base` | Bases views for sources, claims, and fleeting notes. | [Dashboards](dashboards.md) |
| `system/board/board.base` | Bases view over exported Hermes worker cards. | [Kanban board reference](kanban-board.md) |
| `system/patterns/patterns.base` | Bases view over runnable patterns. | [System actions](system-actions.md) |
| `system/worklists/worklists.base` | Bases view over batch screening rows; the Inbox points here with one aggregate work-prompt per batch. | [Dashboards](dashboards.md) |
| `catalog/catalog.base` | Catalog-wide Bases view for papers, people, organizations, venues, datasets, and repositories. | [Document types](document-types.md) |
| `inbox/inbox.base` | Inbox card Bases view, including the `Needs me` surface embedded on the Inbox queue. | [Kanban board reference](kanban-board.md) |
| `notes/hubs/hubs.base` | Bases view over hub notes. | [Dashboards](dashboards.md) |
| `projects/projects.base` | Bases view over project notes, including the refutation-stamp gate. | [Dashboards](dashboards.md) |

The source copies are tracked in [`src/system/`](https://github.com/eranroseman/memoria-vault/tree/main/src/system), [`src/catalog/catalog.base`](https://github.com/eranroseman/memoria-vault/blob/main/src/catalog/catalog.base), and [`src/inbox/inbox.base`](https://github.com/eranroseman/memoria-vault/blob/main/src/inbox/inbox.base). The installer copies them into the runtime vault and stages a golden copy for drift detection.
