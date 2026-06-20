---
title: Use canvas for argument mapping
parent: Project
nav_order: 4
---

# Use canvas for argument mapping

Arrange claim notes spatially in an Obsidian Canvas to find the argument structure before drafting — the cycle's *sketch* phase, engaged by judgment when the argument is tangled, not run on every section.

> This is an optional refinement of the framing produced by [Frame a project](frame-a-project.md), which is the primary path to `projects/<slug>/chosen-framing.md`. The canvas refines or replaces that file once the spatial arrangement is stable.

## When to use it

Open a canvas when you have 8–15 relevant claim notes on a topic and need to see how they fit together before writing. Below 8 notes the argument isn't ready; above 15, split into sections and do one at a time.

## Steps

**1. Create the canvas file.**

Create a `.canvas` file in your project folder, `projects/<slug>/` ([Start a writing project](start-a-writing-project.md)). Name it after the argument section: `chapter-2-receptivity-argument.canvas`.

**2. Collect the notes.**

Drag the relevant claim notes from the file explorer onto the canvas. A hub's `members` list is the natural shopping list. Include Catalog paper entities for key sources if helpful, but primarily use claims — they already state the argument in your words.

**3. Arrange spatially.**

Group notes by sub-argument. Place claims that support the same point together; let `contradicts` pairs face each other. Draw arrows for logical flow: premise → implication → conclusion. Use text cards (no wikilink) for transitional claims that aren't in any note yet — these are gaps.

**4. Identify gaps.**

Any text card not grounded in a claim note is an unverified assertion. Before drafting, either write the claim from a source you hold, or queue the missing source (`Cmd/Ctrl-P` → **Memoria: capture source from URL**, **Memoria: delegate task** → `catalog`, or ask the Co-PI to shape the gap — [Find new sources](../library/find-new-sources.md)).

**5. Build the outline.**

Once the arrangement is stable, write the outline from the canvas groupings: each group becomes a section; the notes in a group become its evidence. Save it as (or fold it into) `projects/<slug>/chosen-framing.md` ([Frame a project](frame-a-project.md)).

**6. Draft.**

Open the canvas in a split pane and draft section by section — yourself, or by delegating sections to the `draft` lane ([Draft with the Writer](draft-with-writer.md)). Keep prose claims tied to claim notes on the canvas, never improvised — see [Draft with the Writer](draft-with-writer.md).

## Conventions

- One canvas per argument cluster or chapter section, not one per paper.
- Canvases are sketches, not knowledge — the claims are the durable units; delete or shelve the canvas when the section is done.
- Never embed a canvas in a draft note — the canvas format does not export through Pandoc ([Export a draft](export-a-draft.md)).

## Verify

- Every text card on the canvas is either grounded in a claim note or queued as a discovery task
- The outline you drafted maps one-to-one onto the canvas groupings

## Related

- Producing the framing the canvas maps: [Frame a project](frame-a-project.md)
- Drafting from the stable arrangement: [Draft with the Writer](draft-with-writer.md)
- Filling exposed gaps: [Find new sources](../library/find-new-sources.md)
- Why claim notes (not canvas cards) are the knowledge unit: [Note body structure](../../explanation/knowledge/note-body-structure.md)
