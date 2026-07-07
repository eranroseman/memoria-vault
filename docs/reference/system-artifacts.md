---
title: System artifacts
parent: System and infrastructure
grand_parent: Reference
nav_order: 4
---

# System artifacts

System artifacts are runtime-vault files owned by the product rather than
ordinary Concept documents. Most are visible to the PI; hidden entries under
`.memoria/` are runtime-owned fixtures or support files.

| Runtime path | What it is | Reference |
| --- | --- | --- |
| `index.md` | Generated OKF-style workspace index over the current bundle roots. | [Operations](operations.md) |
| `bibliography.bib` | Generated BibTeX projection from checked SQLite catalog rows with citekeys. | [Ingest routing](ingest.md) |
| `projects/<slug>/code/<artifact-id>.md` | Typed `code-artifact` record for project companion code, approved argv, declared inputs, and declared outputs. | [Evidence sets](evidence-sets.md) |
| `projects/<slug>/code/<artifact-id>/src/` and `outputs/` | Companion source and generated output directories for a code artifact. | [Evidence sets](evidence-sets.md) |
| `system/vocabulary.md` | Controlled vocabulary for Work `research_area`/`methodology` metadata and claim-bearing note `topics`. | [Vocabulary](vocabulary.md) |
| `.memoria/eval/` | Gold-task fixtures for vault-eval dispatch and scoring. | [Vault eval](vault-eval.md) |
| `.memoria/code-runs/<run-id>/` | Runtime stdout/stderr materialization for a recorded code run. | [Evidence sets](evidence-sets.md) |

The source copies are tracked in
[`vault-template/system/`](https://github.com/eranroseman/memoria-vault/tree/main/vault-template/system),
[`vault-template/.memoria/eval/`](https://github.com/eranroseman/memoria-vault/tree/main/vault-template/.memoria/eval),
and [`vault-template/index.md`](https://github.com/eranroseman/memoria-vault/blob/main/vault-template/index.md).
`bibliography.bib` is generated from checked SQLite catalog rows, and the root,
workspace `index.md` is generated from checked Concept files. The tracked
projection drift check covers all committed projections. Packaged
capability manifests can be inspected through the ignored local cache
`.memoria/index/capability-index.json`.
The installer copies template-owned artifacts into the runtime vault; package or
template refresh is the product-file repair path.

Code execution is unavailable unless
`memoria_vault.runtime.code.runner.execution_availability(vault)` reports a
passing Linux/WSL `bwrap` sandbox proof. Without that proof, code artifacts can
be recorded, but product execution fails closed.
