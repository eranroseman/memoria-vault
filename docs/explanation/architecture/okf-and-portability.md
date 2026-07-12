---
title: OKF and portability
parent: Architecture
grand_parent: Explanation
nav_order: 5
---

# OKF and portability

> **Planned (beta.1 — K1):** Strict OKF production, folder-copy export, and unchecked foreign-bundle import described below are target-state.

Memoria's durability promise is structural: the knowledge outlives the tool.

## The vault is a bundle

Everything in the vault except `.memoria/` is one self-contained Knowledge
Bundle in the [Open Knowledge Format](../../reference/data-model/glossary.md#open-knowledge-format-okf):
plain Markdown, standard links, a generated `index.md`, and a
`bibliography.bib` companion. `cat` works. If Memoria is removed, the corpus,
notes, projects, and bibliography remain readable and editable with any tool.

`.memoria/` is engine-space: verdicts, provenance, queues, indexes, blobs —
trust state *about* the knowledge, never the knowledge itself. A bundle
copied without `.memoria/` loses its verdict state by design: trust is
re-derived, not transported.

## An opinionated producer

Memoria is a *strict producer* of OKF: its bundles are OKF-consumable, but
internally the files carry Memoria's typed frontmatter and conventions.
Export is a copy of the bundle folder — no transformation step. Import of a
foreign bundle takes the normal source-import path: content re-enters as
unchecked and earns its way through the gates like any other source.

## Nested project bundles

> **Planned (beta.1 — K1/W2):** Detachability enforcement and the complete project-close harvest/archive lifecycle are target-state.

Each `projects/<slug>/` is itself a nested, detachable OKF bundle. Projects
may reference vault knowledge freely; permanent knowledge never links into a
project (the one-way rule that keeps projects detachable); project close
harvests durable claims back into the vault before the working bundle
archives.

## Related

- [What Memoria is](../rationale/foundations/what-memoria-is.md) — the bundle constitution.
- [The vault](vault.md) — bundle roots and layout.
- [Consistency model](consistency-model.md) — how files and engine state stay honest.
