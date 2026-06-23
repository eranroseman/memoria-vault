---
title: Knowledge
parent: Explanation
nav_order: 3
has_children: true
permalink: /explanation/knowledge/
---

# The knowledge model

The vault stores durable knowledge organized type-first into category folders, with lifecycle carried as a frontmatter state. Understanding the knowledge model means understanding what makes knowledge _durable_, how the vault's organization serves that goal, and why certain moves are allowed and others aren't. Knowledge is the durable counterpart to transient _work_: work lives on the board as cards and dies at `archived`, while knowledge lives in the vault and persists — a distinction the board section develops in [Cards and notes are different things](../workflows/board-as-state-machine.md#cards-and-notes-are-different-things).

> **Lineage.** This section's core ideas — atomic notes, links over folders, maturing notes, and Maps of Content — descend directly from Luhmann's **Zettelkasten** method and its modern "evergreen notes" successors. Memoria's contribution is not the method but its _delegation_: agents do the Zettelkasten bookkeeping (linking, classifying, drift detection) the method demands while the human keeps the intellectual work. The full intellectual debt is traced in [Intellectual foundations](../overview/intellectual-foundations.md#luhmanns-zettelkasten); the pages below note where each specific idea is borrowed.

## Documents in this section

| Page                                                               | What it covers                                                                                                                           |
| ------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| [Document types and epistemic roles](document-types.md)                    | The three epistemic roles (source / synthesis / working) behind the document types, and why agent permissions follow from them.              |
| [The knowledge cycle](knowledge-cycle.md)                          | The progression from ingested source to written output, and why the vault compounds rather than merely accumulates.                      |
| [Your first month](your-first-month.md)                            | The tempo of that cycle over your first weeks of real use — when to capture, distill, produce, and review so the vault compounds, not rots. |
| [Note body structure](note-body-structure.md)                      | Why source notes, claim notes, and hubs have the body sections they do, and what each section makes the note able to do.                  |
| [Lifecycle, not topic — and state, not folders](lifecycle-over-topic.md) | Why folders encode a note's type rather than subject, why lifecycle is a frontmatter state rather than a folder, and how topics live in frontmatter and links instead. |
| [Why promotion is gated](promotion-model.md)                       | What promotion means, the one-way promotion map and its disallowed moves, and why the human gate sits at the synthesis boundary.         |
| [Vocabulary discipline](vocabulary-discipline.md)                  | Why the classification fields are kept separate, why vocabulary consolidation is deferred, and how term drift fails silently.            |
| [Common pitfalls](common-pitfalls.md)                              | The recurring failure modes of a vault built this way, and the automation-boundary principle underneath them.                            |
| [Why hubs](hubs-and-navigation.md)                                 | Why the link-first vault needs a human-curated navigation layer, and why hubs are authored, threshold-prompted, and review-gated.        |

For the complete document-type reference (fields, templates, lifecycle tables), see [Document types](../../reference/document-types.md).
