---
topic: decisions
id: 119
title: "Concept schemas own field, home, read-state, and form contracts"
nav_exclude: true
status: accepted
date_proposed: 2026-06-23
date_resolved: 2026-06-23
assumes: [52, 116]
supersedes: []
superseded_by: []
---

# ADR-119: Concept schemas own field, home, read-state, and form contracts

## Context

Memoria's document contract used to be split across ADR prose, schema YAML, folder
maps, templates, Modal Forms, and hand-coded detectors. That made old decisions about
type names, lifecycle values, forms, and folder homes drift after the alpha.12 schema
simplification.

The current contract is smaller and stricter: every durable user-facing object is a
**Concept**, every Concept has one type schema, and the generated reference pages are
consumer views of those machine-readable sources.

## Decision

The authoritative Concept contract has four owners:

1. `vault-template/.memoria/schemas/types/*.yaml` owns the field contract for each
   Concept type: required fields, optional fields, enums, `gated`, and
   `initial_check_status`.
2. `vault-template/.memoria/schemas/folders.yaml` owns placement: category roots,
   bundle roots, type homes, staging roots, quarantine, and installer skeleton paths.
3. `check_status` is the universal read-state gate for Concepts:
   `unchecked -> checked -> quarantined`. It is not a folder move and not a workflow
   lifecycle. Type-specific fields such as `source.lifecycle` and `note.status` remain
   local schema fields.
4. Obsidian Modal Forms are generated UI entry points, not schema authority. They may
   collect values that are mapped into frontmatter or body text, but validation remains
   the Concept schema plus shared loader.

The accepted alpha.12 Concept roster is:

| Category | Types | Homes |
| --- | --- | --- |
| Catalog | `source`, `person`, `organization`, `venue` | `catalog/sources`, `catalog/entities` |
| Knowledge | `digest`, `note`, `hub`, `project` | `knowledge/digests`, `knowledge/notes`, `knowledge/hubs`, `knowledge/projects` |
| Capability | `operation`, `skill`, `mcp`, `workflow` | `capabilities/operations`, `capabilities/skills`, `capabilities/mcp`, `capabilities/workflows` |

Generated references such as `document-types.md` and `frontmatter.md` must be
regenerated from the schema sources. They must not restate a competing type roster,
home map, or read-state chain.

Inbox cards are not durable Concept types in this model. They are generated attention
projections over Concept and operational state; their evidence and body shape are owned
by ADR-54's human-decision contract.

Project theses do not need a dedicated type. A project may point its `thesis` field at
a checked `note`; Project gate and argument-graph logic derive from that relationship.

## Consequences

- Retiring stale ADRs must leave this ADR, the schema files, and generated reference
  pages in agreement.
- Type additions, field additions, home changes, read-state changes, and form-generation
  changes are schema changes and must update the schema source plus generated references.
- The Linter, pre-commit hook, worker promotion code, installer skeleton tests, and docs
  generators all read the same schema/folder sources. A behavior that only appears in
  prose is not an enforced boundary.
- Folder names no longer double as workflow state. Quarantine and staging are machine
  areas under `.memoria/`; checked Concepts stay in their type homes.

## Alternatives considered

**Keep one ADR per retired schema-era rule.** Rejected: separate ADRs for forms, type
names, folder layout, lifecycle, and thesis type had become stale mirrors of the same
contract.

**Make Modal Forms the source of truth.** Rejected: forms are a human input surface.
They cannot validate agent writes, worker promotion, installer skeletons, or pre-commit
checks.

**Use workflow folders as state.** Rejected: moving files to express read status breaks
links and duplicates the schema-owned `check_status` gate.

## Related

- **Refines:** [ADR-116](116-obsidian-surface-architecture.md) (one definition, many
  surfaced views).
- **Depends on:** [ADR-52](52-links-vs-relationships.md) (typed relationships).
- **Generated views:** [Document types](../reference/document-types.md),
  [Frontmatter fields](../reference/frontmatter.md), and
  [On-disk layout](../reference/on-disk-layout.md).
