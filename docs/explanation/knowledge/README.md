---
title: Knowledge
parent: Explanation
nav_order: 2
has_children: true
permalink: /explanation/knowledge/
---

# The knowledge model

The vault stores durable knowledge as type-first Concepts with semantic
frontmatter and body text. Verdict state lives in SQLite and read-API responses,
not in frontmatter. Understanding the knowledge model means understanding what
makes knowledge _durable_, how the vault's organization serves that goal, and why
certain moves are allowed and others aren't. Knowledge is the durable counterpart
to transient _work_: work lives as operation requests and attention, while
knowledge lives in the vault and persists — a distinction the control-plane
section develops in [Requests and notes are different things](../execution/control-plane/states.md#requests-and-notes-are-different-things).

> **Lineage.** This section's core ideas — atomic notes, links over folders,
> checked read boundaries, and Maps of Content — descend directly from Luhmann's
> **Zettelkasten** method and its modern ["evergreen notes"](../../reference/evidence-and-integrations/bibliography.md#matuschak-evergreen)
> successors. Memoria's contribution is not the method but its _delegation_:
> agents do the Zettelkasten bookkeeping (linking, classifying, drift detection)
> the method demands while the human keeps the intellectual work. The full
> intellectual debt is traced in [Intellectual foundations](../rationale/foundations/intellectual-foundations.md#luhmanns-zettelkasten);
> the pages below note where each specific idea is borrowed.

## Documents in this section

| Page                                                               | What it covers                                                                                                                           |
| ------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| [Document types and epistemic roles](document-types.md)                    | The three epistemic roles (source / synthesis / working) behind the document types, and why agent permissions follow from them.              |
| [The knowledge cycle](knowledge-cycle.md)                          | The progression from ingested source to written output, including project slices, exploration, and why the vault compounds rather than merely accumulates.                      |
| [Note body structure](note-body-structure.md)                      | Why works, notes, hubs, and projects have distinct bodies, and what each structure makes the Concept able to do.                  |
| [Promotion and the write boundary](promotion-and-gated-zones.md)                       | What promotion means, how the trusted writer protects checked readers, and why PI curation sits at the synthesis boundary.         |
| [Vocabulary discipline](vocabulary-discipline.md)                  | Why the classification fields are kept separate, why vocabulary stabilization is staged, and how term drift fails silently.            |
| [Common pitfalls](common-pitfalls.md)                              | The recurring failure modes of a vault built this way, and the automation-boundary principle underneath them.                            |
| [Consequence propagation](consequence-propagation.md)              | How typed graph edges expose the blast radius of knowledge changes and route each dependent to the right disposition.                    |

For the document-type roster, see [Document types](../../reference/data-model/document-types.md).
For field grammar, see [Frontmatter fields](../../reference/data-model/frontmatter.md). For
the current task surface that follows from this model, see the [Knowledge how-to
guides](../../how-to-guides/knowledge/).
