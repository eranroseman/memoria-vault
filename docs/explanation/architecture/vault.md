---
title: The vault
parent: Architecture
grand_parent: Explanation
nav_order: 1
---

# The vault

The vault is where durable knowledge lives. Everything else in Memoria - the
CLI, worker, operations, dashboards, and optional adapters - exists to serve it.
This page explains the alpha.15 workspace shape, Concept homes, and write boundary.

---

## Bundle roots

The top level has three OKF-compatible bundle roots plus workspace-level state.
The knowledge graph is a network, not a pipeline: direction lives in `steering.md`,
project framing, typed links, and `check_status`, not in lifecycle folders.

```text
<vault-root>/
├── steering.md     ← PI-authored program memory
├── catalog/        ← source and entity records
├── knowledge/      ← Works, notes, hubs, projects
├── system/         ← visible infrastructure: templates, dashboards, eval, logs
└── .memoria/       ← hidden runtime: schemas, SQLite request state, staging, quarantine
```

The type to folder-home map is machine-read
(`.memoria/schemas/folders.yaml`) and is the single source for validators,
projection generators, installer skeleton, and tests.

## Types and their homes

Each bundle root carries a different role. The full roster and folder map live
in [Document types](../../reference/document-types.md).

| Area | Examples | Trust posture |
| --- | --- | --- |
| Catalog | source and entity rows | Objective records from capture/import; checked before consumption. |
| Knowledge | work, note, hub, project | The working graph. Works can be machine-owned digests; notes and hub curation are PI judgment. |
| System | templates, dashboards, eval, logs | Visible infrastructure and generated projections; product operations live in the installed package. |

## Write Boundary

Machine writes, promotions, generated projections, journal rows, and
`check_status` transitions go through the worker. PI edits are direct file
edits; the worker observes and backfills them into the journal. Foreign or
untraced bundle writes are quarantined by the integrity scan before checked
readers can consume them.

## Archived is a state, not a folder

Archive/retraction state is runtime state, not a folder move. Current readers use
the DB/read API `check_status = checked` verdict; unchecked and quarantined Concepts stay out of the
checked index and Ask path.

The same trust split applies to connections: `links:` are authored note connections, while entity `relationships` are given facts from ingest ([ADR-126](../../adr/126-four-type-knowledge-model.md)). Field contracts live in [Frontmatter fields](../../reference/frontmatter.md).

## Generated views; the Linter keeps them sound

Catalog records and knowledge Concepts surface through generated indexes and
optional editor views. Views are projections; Concept frontmatter is governed by
[ADR-126](../../adr/126-four-type-knowledge-model.md), and catalog rows that feed
bibliography/materialization are governed by
[ADR-124](../../adr/124-standalone-catalog-citation-authority.md).

Bases has no schema or constraints. The **Linter operation** supplies that layer: it validates records against `.memoria/schemas/`, flags drift, blocks malformed git-tracked writes at pre-commit, and monitors live edits through scheduled or CI sweeps. A bad in-app edit can briefly appear in a Base before the next sweep; that window is accepted under the solo premise. Shipped product-file repair comes from package/template refresh, not an in-vault restore baseline.

---

## Related

- The full stack the vault sits under: [Architecture](README.md)
- The operations that maintain the vault: [Operations](../operations.md)
- The write boundary: [Promotion and the write boundary](../knowledge/promotion-and-gated-zones.md)
