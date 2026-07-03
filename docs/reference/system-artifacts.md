---
title: System artifacts
parent: System and infrastructure
grand_parent: Reference
---

# System artifacts

Visible system artifacts are runtime-vault files the PI can inspect from
Obsidian. They are not hidden `.memoria/` internals.

| Runtime path | What it is | Reference |
| --- | --- | --- |
| `index.md`, `catalog/index.md`, `knowledge/index.md` | Generated OKF-style workspace and bundle indexes. | [Operations](operations.md) |
| `knowledge/_views/index.md` | Generated knowledge view summary from checked knowledge Concepts. | [Operations](operations.md) |
| `references.bib` | Generated BibTeX projection from checked SQLite catalog rows with citekeys. | [Ingest routing](ingest.md) |
| `system/vocabulary.md` | Controlled vocabulary for `research_area`, `methodology`, and claim `topics`. | [Vocabulary](vocabulary.md) |
| `system/eval/` | Gold-task fixtures for vault-eval dispatch and scoring. | [Vault eval](vault-eval.md) |
| `catalog/catalog.base` | Bases view over `catalog/sources/`. | [Document types](document-types.md) |
| `knowledge/views/knowledge.base` | Bases views over `digest`, `note`, `hub`, and `project` Concepts. | [Dashboards](dashboards.md) |

The source copies are tracked in
[`vault-template/system/`](https://github.com/eranroseman/memoria-vault/tree/main/vault-template/system),
[`vault-template/catalog/catalog.base`](https://github.com/eranroseman/memoria-vault/blob/main/vault-template/catalog/catalog.base),
and
[`vault-template/knowledge/views/knowledge.base`](https://github.com/eranroseman/memoria-vault/blob/main/vault-template/knowledge/views/knowledge.base).
`references.bib` is generated from checked SQLite catalog rows (with source
Concept fallback only when no catalog rows exist), and the root, bundle, and
knowledge view `index.md` files are generated from checked Concept files. The
tracked projection drift check covers all committed projections. Packaged
capability manifests can be inspected through the ignored local cache
`.memoria/index/capability-index.json`.
The installer copies template-owned artifacts into the runtime vault; package or
template refresh is the product-file repair path.
