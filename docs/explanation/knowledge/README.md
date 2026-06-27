---
title: Knowledge
parent: Explanation
nav_order: 3
has_children: true
permalink: /explanation/knowledge/
---

# The knowledge model

The vault stores durable knowledge organized type-first into category folders, with lifecycle carried as a frontmatter state. Understanding the knowledge model means understanding what makes knowledge _durable_, how the vault's organization serves that goal, and why certain moves are allowed and others aren't. Knowledge is the durable counterpart to transient _work_: work lives on the board as cards and dies at `archived`, while knowledge lives in the vault and persists — a distinction the board section develops in [Cards and notes are different things](../workflows/board-as-state-machine.md#cards-and-notes-are-different-things).

> **Lineage.** This section's core ideas — atomic notes, links over folders, maturing notes, and Maps of Content — descend directly from Luhmann's **Zettelkasten** method and its modern "evergreen notes" successors. Memoria's contribution is not the method but its _delegation_: agents do the Zettelkasten bookkeeping (linking, classifying, drift detection) the method demands while the human keeps the intellectual work. The full intellectual debt is traced in [Intellectual foundations](../../design/intellectual-foundations.md#luhmanns-zettelkasten); the pages below note where each specific idea is borrowed.

## Documents in this section

| Page                                                               | What it covers                                                                                                                           |
| ------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| [Document types and epistemic roles](document-types.md)                    | The three epistemic roles (source / synthesis / working) behind the document types, and why agent permissions follow from them.              |
| [The knowledge cycle](knowledge-cycle.md)                          | The progression from ingested source to written output, and why the vault compounds rather than merely accumulates.                      |
| [Note body structure](note-body-structure.md)                      | Why source notes, claim notes, and hubs have the body sections they do, and what each section makes the note able to do.                  |
| [Why promotion is gated](promotion-model.md)                       | What promotion means, the one-way promotion map and its disallowed moves, and why the human gate sits at the synthesis boundary.         |
| [Vocabulary discipline](vocabulary-discipline.md)                  | Why the classification fields are kept separate, why vocabulary consolidation is deferred, and how term drift fails silently.            |
| [Common pitfalls](common-pitfalls.md)                              | The recurring failure modes of a vault built this way, and the automation-boundary principle underneath them.                            |

For the complete document-type reference (fields, templates, lifecycle tables), see [Document types](../../reference/document-types.md). For the practice cadence that follows from this model, see [Your first month](../../how-to-guides/knowledge/your-first-month.md).
