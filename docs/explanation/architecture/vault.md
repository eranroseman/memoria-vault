---
title: The vault
parent: Architecture
grand_parent: Explanation
nav_order: 1
---

# The vault

The vault is where durable knowledge lives. Everything else in Memoria - the
CLI, worker, operations, dashboards, and optional adapters - exists to serve it.
This page explains the alpha.16 workspace shape, Concept homes, and write boundary.

---

## Bundle roots

The top level has alpha.16 bundle roots plus workspace-level state.
The knowledge graph is a network, not a pipeline: direction lives in `steering.md`,
project framing, typed links, and `check_status`, not in lifecycle folders.

```text
<vault-root>/
├── steering.md     ← PI-authored program memory
├── works/          ← Work bundles: record, full text, digest, source assets
├── sources/        ← Source notes
├── notes/          ← Claim and question notes
├── hubs/           ← Curated topic hubs
├── projects/       ← Project bundles
├── inbox/          ← Attention projections
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
| Knowledge | work, digest, source-note, note, hub, project | The working graph. Work records and digests can be machine-owned; source-notes, notes, hubs, and project curation carry PI judgment. |
| System | templates, dashboards, eval, logs | Visible infrastructure and generated projections; product operations live in the installed package. |

## Write Boundary

Machine writes, promotions, generated projections, journal rows, and
`check_status` transitions go through the worker. PI edits are direct file
edits; the worker observes and backfills them into the journal. Foreign or
untraced bundle writes are quarantined by the integrity scan before checked
readers can consume them.

## Actor-kinds and the write path

Three kinds of actor work across the structural layers (see the [layer
diagram](README.md)):

| Actor-kind | Who | Trait |
| --- | --- | --- |
| **PI** | the human (L1) | judgment, curation, and attention disposition |
| **Agents** | runner-backed operations or optional adapters | posture + LLM judgment; propose, never dispose |
| **Operations** | ingest · search · sweeps · Linter (L4) | deterministic, no posture; never on the board |

The "is it an agent or an operation?" question is decided by posture and LLM
judgment, not invocation style. Agents propose; only the trusted worker
materializes checked outputs, and the PI separately disposes attention/curation
decisions. Why that boundary is structural rather than a convention is [Why the
review gate is structural](../../design/why-review-gate-is-structural.md).

The strict each-layer-depends-only-on-the-one-below contract holds along this
machine write path only — it doesn't extend above to the PI's direct file
edits. The write boundary above is the trusted worker plus staging, read
barrier, quarantine, journal, and git history; optional adapters may add
pre-tool gates on top of that stack, but may not replace it.

## Archived is a state, not a folder

Archive/retraction state is runtime state, not a folder move. Current readers use
the DB/read API `check_status = checked` verdict; unchecked and quarantined Concepts stay out of the
checked index and Ask path.

The same trust split applies to connections: `links:` are authored note connections, while entity `relationships` are given facts from ingest ([the four-type Concept model with meaning-only frontmatter](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)). Field contracts live in [Frontmatter fields](../../reference/frontmatter.md).

## Generated views; the Linter keeps them sound

Catalog records and knowledge Concepts surface through generated indexes and
optional editor views. Views are projections; Concept frontmatter is governed by
[the four-type Concept model with meaning-only frontmatter](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md), and catalog rows that feed
bibliography/materialization are governed by the decision that
[standalone catalog is the citation authority](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md).

Bases has no schema or constraints. The **Linter operation** supplies that layer: it validates records against `.memoria/schemas/`, flags drift, blocks malformed git-tracked writes at pre-commit, and monitors live edits through scheduled or CI sweeps. A bad in-app edit can briefly appear in a Base before the next sweep; that window is accepted under the solo premise. Shipped product-file repair comes from package/template refresh, not an in-vault restore baseline.

---

## Related

- The full stack the vault sits under: [Architecture](README.md)
- The operations that maintain the vault: [Operations](../operations.md)
- The write boundary: [Promotion and the write boundary](../knowledge/promotion-and-gated-zones.md)
