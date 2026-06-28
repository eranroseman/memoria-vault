---
name: schema-change
description: Implement or review changes to Memoria document schemas, folder homes, gated prefixes, calibration, templates, Bases, dashboards, linter validation, and installer skeleton without cross-file drift.
---

# Schema change

Use this skill when adding or changing a document type, frontmatter field, enum,
folder home, gated/transient prefix, skeleton directory, or calibrated threshold.

## Authority and maps

Read:

1. [`AGENTS.md`](../../../AGENTS.md)
2. [Source-of-truth map](../../system/source-of-truth-map.md)
3. [Change-impact map](../../system/change-impact-map.md)
4. [Test selection](../../system/test-selection.md)

## Change procedure

1. State the contract change precisely:
   - Type and field name
   - Required, optional, `required_any`, literal, or enum behavior
   - Lifecycle implications
   - Folder home and whether the type is gated or transient
   - Migration impact on existing vaults
2. Edit the canonical YAML first:
   - `schemas/types/<type>.yaml` for fields and enums
   - `schemas/folders.yaml` for homes, prefixes, and skeleton
   - `schemas/calibration.yaml` for thresholds
3. Inspect and update affected consumers:
   - Matching `vault-template/system/templates/<type>.md`
   - `.base` views and dashboard queries
   - Shared card writer or engine emitters
   - Linter/pre-commit behavior
   - Installer skeleton and golden-copy behavior
   - Policy/pattern fallback constants when gated prefixes change
   - Frontmatter, document-type, layout, and workflow documentation
4. Preserve invariants:
   - Every type has exactly one home and a matching type literal.
   - Lifecycle values are an ordered subset of the universal chain.
   - A type's `gated` flag agrees with its home under `gated_prefixes`.
   - Every home appears in the installer skeleton.
   - Templates begin schema-valid.
   - Bases and dashboards reference fields emitted by schemas/templates.
   - Unknown fields remain allowed unless an ADR changes that contract.
   - Proposal, verification, and work-prompt card shapes remain distinct.
5. Decide whether migration is needed. A breaking schema or folder change
   requires an ADR, migration guidance, and tests for old vault state.
6. Run focused schema tests from `test-selection.md`, relevant component tests,
   and the full gate before PR handoff.

## Review-only mode

When asked only to review, do not edit. Compare the diff against every consumer
in the change-impact map and report missing updates or unsafe migration behavior.

## Output

For implementation, summarize the canonical contract change, synchronized
consumers, migration behavior, and verification. For review, use the
[review report template](../../templates/review-report.md).
