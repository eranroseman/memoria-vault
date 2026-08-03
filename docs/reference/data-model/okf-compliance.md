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

- The vault targets **OKF v0.2**
  ([spec](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md));
  the root `index.md` declares `okf_version: "0.2"`.
- Every non-reserved Markdown file in the bundle tree has parseable YAML
  frontmatter with a non-empty `type` — bundle roots, the vault root, and
  `system/` alike.
- Reserved files follow their reserved structure: `index.md` carries only
  the root version declaration; a `log.md`, if ever present, carries no
  frontmatter.
- The **OKF Concept ID** is path-derived (the file path minus `.md`); a
  Concept's **internal id** (a ULID for `note`/`hub`/`project`; the source
  `work_id` for `digest`/`fulltext`; the artifact id for `code-artifact` —
  see [Frontmatter fields](frontmatter.md#other-universal-fields)) is
  producer metadata, not OKF identity. (Planned: G3, beta.1/B1.)
- Provenance is first-class: the trusted writer stamps `generated` at
  staging and derives `sources` from derivation inputs; authored `sources`
  entries for external material are preserved as written.
- Acceptance records a `verified` confirmation entry using the OKF actor
  grammar (`human:<id>`, `<producer>/<version>`, `process:<id>`). An entry
  states what was confirmed as of its `at` time and nothing after it:
  content can change following a confirmation without the entry being
  removed (spec §5.2). The entry is replaced by the next acceptance and
  stripped when content is re-staged; the current judgment state itself
  lives engine-side, never in the file.
- The engine's own judgment state never travels as authority — it stays in
  `.memoria/`, and an OKF trust field in a file is a signal, never a grant.
- Imported or copied content re-enters through the normal gates, and a
  foreign bundle's trust fields are read as signals like any other.
  **Planned beta.1 — K1.**
- Deliberate omissions, each additive later at zero migration cost:
  `status` (absent means `stable`; staging is the draft plane;
  `superseded`/`archived` carry deprecation), `stale_after` (no TTL
  semantics yet), the `Attested Computation` type (no instances; the
  spec tolerates unknown types), and `log.md` (optional per OKF §9;
  not generated).
- OKF-facing relationships and citations use standard Markdown links
  (bundle-relative); wikilinks remain a local authoring affordance. **Planned
  beta.1 — K1.**
- Export is a copy of the bundle folder (vault minus `.memoria/`), taken from
  a clean committed state, with no transformation step. **Planned beta.1 —
  K1.**

## Related

- [Frontmatter](frontmatter.md) — the per-type field contract.
- [Glossary](glossary.md#open-knowledge-format-okf) — OKF, Knowledge Bundle.
