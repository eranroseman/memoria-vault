---
title: OKF compliance contract
parent: Reference data model
nav_order: 6
grand_parent: Reference
---

# OKF compliance contract

What "the vault is an OKF bundle" requires of every file. Reference for the
conformance bar; the rationale lives in
[OKF and portability](../../explanation/architecture/okf-and-portability.md).

## The bar

- Every non-reserved `.md` file has parseable YAML frontmatter with a
  non-empty `type`.
- Reserved files (`index.md`, `log.md`) follow their reserved structure.
- The **OKF Concept ID** is path-derived (the file path minus `.md`); a
  Concept's **internal id** (a ULID for `note`/`hub`/`project`; the source
  `work_id` for `digest`/`fulltext`; the artifact id for `code-artifact` —
  see [Frontmatter fields](frontmatter.md#other-universal-fields)) is
  producer metadata, not OKF identity. (Planned: G3, alpha.22/B1.)
- OKF-facing relationships and citations use standard Markdown links
  (bundle-relative); wikilinks remain a local authoring affordance. **Planned
  beta.1 — K1.**
- Verdicts and judgment state never appear in frontmatter — trust state is
  engine-space (`.memoria/`), not bundle content.
- Imported or copied OKF content re-enters as **unchecked** and earns its
  status through the normal gates; check states never travel in files.
  **Planned beta.1 — K1.**
- Export is a copy of the bundle folder (vault minus `.memoria/`), taken from
  a clean committed state, with no transformation step. **Planned beta.1 —
  K1.**

## Related

- [Frontmatter](frontmatter.md) — the per-type field contract.
- [Glossary](glossary.md#open-knowledge-format-okf) — OKF, Knowledge Bundle.
