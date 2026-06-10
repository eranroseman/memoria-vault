---
title: Knowledge
parent: Explanation
nav_order: 3
has_children: true
permalink: /explanation/knowledge/
---

# The knowledge model

The vault stores durable knowledge organized by lifecycle stage. Understanding the knowledge model means understanding what makes knowledge _durable_, how the vault's organization serves that goal, and why certain moves are allowed and others aren't. Knowledge is the durable counterpart to transient _work_: work lives on the board as cards and dies at `archived`, while knowledge lives in the vault and persists — a distinction the board section develops in [Cards and notes are different things](../workflows/board-as-state-machine.md#cards-and-notes-are-different-things).

> **Lineage.** This section's core ideas — atomic notes, links over folders, maturing notes, and Maps of Content — descend directly from Luhmann's **Zettelkasten** method and its modern "evergreen notes" successors. Memoria's contribution is not the method but its _delegation_: agents do the Zettelkasten bookkeeping (linking, classifying, drift detection) the method demands while the human keeps the intellectual work. The full intellectual debt is traced in [Intellectual foundations](../overview/intellectual-foundations.md#luhmanns-zettelkasten); the pages below note where each specific idea is borrowed.

## Documents in this section

| Page                                                               | What it covers                                                                                                                           |
| ------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| [Note types and epistemic roles](note-types.md)                    | The three epistemic roles (source / synthesis / working) behind the note types, and why agent permissions follow from them.              |
| [The knowledge cycle](knowledge-cycle.md)                          | The progression from ingested source to written output, and why the vault compounds rather than merely accumulates.                      |
| [Note body structure](note-body-structure.md)                      | Why paper-notes, claim-notes, and MOCs have the body sections they do, and what each section makes the note able to do.                  |
| [Lifecycle, not topic — and state, not folders](lifecycle-over-topic.md) | Why folders encode lifecycle stage rather than subject, what breaks if they don't, and how topics live in frontmatter and links instead. |
| [Why promotion is gated](promotion-model.md)                       | What promotion means, the one-way promotion map and its disallowed moves, and why the human gate sits at the synthesis boundary.         |
| [Vocabulary discipline](vocabulary-discipline.md)                  | Why the classification fields are kept separate, why vocabulary consolidation is deferred, and how term drift fails silently.            |
| [Common pitfalls](common-pitfalls.md)                              | The recurring failure modes of a vault built this way, and the automation-boundary principle underneath them.                            |

For the complete note-type reference (fields, templates, lifecycle tables), see [Note types](../../reference/note-types.md).
