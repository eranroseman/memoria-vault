---
title: Document types
parent: Reference data model
nav_order: 2
grand_parent: Reference
---

# Document types

The authoritative document-type contract is the schema directory, not this page:

- Type schemas: `src/memoria_vault/product/workspace_seed/.memoria/schemas/types/*.yaml`
- Type homes and skeleton folders: `src/memoria_vault/product/workspace_seed/.memoria/schemas/folders.yaml`
- Loader and validator: `src/memoria_vault/runtime/vocabulary/schema.py`

Each type schema declares its `category`, `concept_type` registry membership,
`required` fields, `optional` fields, and `enums`-backed fields, plus optional
`required_when` and `forbidden` blocks. Folder home is not a type-schema key —
it lives in `folders.yaml`'s `homes:` map. There is no "initial read state" in
frontmatter either: `check_status` lives in SQLite only, never in a Concept
file (see [Verdict state is not
frontmatter](frontmatter.md#verdict-state-is-not-frontmatter)). The linter,
pre-commit hook, trusted writer, and tests read those YAML files directly.

The current schema defines 6 document types: `code-artifact`, `digest`,
`fulltext`, `hub`, `note`, and `project`.
Attention and action state are generated request/queue surfaces, not Concept
types in the vault schema.
Non-Concept documents still declare a `type` for OKF conformance —
`attention` on inbox cards, `system` on infrastructure pages, `outline` and
`draft` on project working documents — without a per-type schema; only the
six types above are schema-validated Concepts.

For field grammar and validation behavior, see [Frontmatter fields](frontmatter.md).

Project `outline.md`, `draft.md`, and `code-artifact` records are project
artifacts, not new human knowledge Concept types. Evidence-set markers inside
drafts derive SQLite `evidence_sets` rows; the marker/DB contract is documented
in [Evidence sets](../control-and-policy/evidence-sets.md).

## Related

- Field kinds and enum values (no full per-type table exists; the schema
  directory above is authoritative): [Frontmatter fields](frontmatter.md)
- The folder tree the homes map into: [On-disk layout](../system/on-disk-layout.md)
- What enforces the schemas: [Linter: detectors and auto-fix](../analysis-and-surfaces/linter.md) and
  [Policy gate](../control-and-policy/policy-mcp.md)
