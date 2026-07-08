---
title: The vault
parent: Architecture
grand_parent: Explanation
nav_order: 1
---

# The vault

The vault is where durable knowledge lives. Everything else in Memoria - the
CLI, worker, operations, dashboards, and optional adapters - exists to serve it.
This page explains why the workspace is the durable knowledge substrate and why
machine writes pass through a worker boundary.

---

## Bundle roots

The top level separates human knowledge, generated support files, and hidden
runtime state. The knowledge graph is a network, not a pipeline: direction lives
in steering, project framing, typed links, and read state, not in lifecycle
folders.

The full folder map lives in [On-disk layout](../../reference/system/on-disk-layout.md)
and [Document types](../../reference/data-model/document-types.md). This page owns the
rationale: type homes give the policy gate stable write boundaries, while links
and state carry the facts that change.

## Write Boundary

Machine writes, promotions, generated projections, journal rows, and
`check_status` transitions go through the worker. PI edits are direct file
edits; the worker observes and backfills them into the journal. Foreign or
untraced bundle writes are quarantined by the integrity scan before read
surfaces that require passing checks can consume them.

## Actor-kinds and the write path

The PI owns judgment, curation, and attention disposition. Runner-backed agents
and optional adapters may propose; deterministic operations may report or
materialize bounded outputs. Only the trusted worker materializes outputs after
runtime checks, and the PI separately disposes attention and curation decisions. Why
that boundary is structural rather than a convention is [Why the review gate is
structural](../rationale/boundaries/why-review-gate-is-structural.md).

The strict each-layer-depends-only-on-the-one-below contract holds along this
machine write path only — it doesn't extend above to the PI's direct file
edits. The write boundary above is the trusted worker plus staging, read
barrier, quarantine, journal, and git history; optional adapters may add
pre-tool gates on top of that stack, but may not replace it.

## Archived is a state, not a folder

Archive/retraction state is runtime state, not a folder move. Current readers use
the DB/read API `check_status = checked` verdict; unchecked and quarantined Concepts stay out of the
checked index and Ask path.

The same trust split applies to connections: `links:` are authored note connections, while entity `relationships` are given facts from ingest. Field contracts live in [Frontmatter fields](../../reference/data-model/frontmatter.md).

## Generated views; the Linter keeps them sound

Catalog records and knowledge Concepts surface through generated indexes and
optional editor views. Views are projections; Concept frontmatter is governed by
the YAML schemas under `.memoria/schemas/`, and catalog rows that feed
bibliography/materialization are governed by the decision that
[standalone catalog is the citation authority](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md).

Optional editor views have no schema or constraints of their own. The **Linter
operation** supplies that layer: it validates records against
`.memoria/schemas/`, flags drift, blocks malformed git-tracked writes at
pre-commit, and monitors live edits through manual, operator-managed, or CI
sweeps. A bad in-app edit can briefly appear in an optional view before the next
sweep; that window is accepted under the solo premise. Shipped product-file
repair comes from package-seed refresh, not an in-vault restore baseline.

---

## Related

- The full stack the vault sits under: [Architecture](README.md)
- The operations that maintain the vault: [Operations](../execution/operations.md)
- The write boundary: [Promotion and the write boundary](../knowledge/promotion-and-gated-zones.md)
