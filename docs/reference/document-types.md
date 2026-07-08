---
title: Document types
parent: Reference
nav_order: 3
---

# Document types

The authoritative document-type contract is the schema directory, not this page:

- Type schemas: `src/memoria_vault/product/workspace_seed/.memoria/schemas/types/*.yaml`
- Type homes and skeleton folders: `src/memoria_vault/product/workspace_seed/.memoria/schemas/folders.yaml`
- Loader and validator: `src/memoria_vault/runtime/subsystems/lib/schema.py`

Each type schema declares its category, folder home, initial read state, required
fields, optional fields, and enum-backed fields. The linter, pre-commit hook,
trusted writer, and tests read those YAML files directly.

The current schema defines 6 document types: `code-artifact`, `digest`,
`fulltext`, `hub`, `note`, and `project`.

For field grammar and validation behavior, see [Frontmatter fields](frontmatter.md).

Project `outline.md`, `draft.md`, and `code-artifact` records are project
artifacts, not new human knowledge Concept types. Evidence-set markers inside
drafts derive SQLite `evidence_sets` rows; the marker/DB contract is documented
in [Evidence sets](evidence-sets.md).

## Related

- Field kinds, enums, and per-type field inventory:
  [Frontmatter fields](frontmatter.md)
- Retired Inbox card status: [Inbox card fields](inbox-card-fields.md)
- The folder tree the homes map into: [On-disk layout](on-disk-layout.md)
- What enforces the schemas: [Linter: detectors and auto-fix](linter.md) and
  [Policy gate](policy-mcp.md)
