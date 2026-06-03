---
title: How to use canvas for argument mapping
parent: Writing
nav_order: 5
---

# How to use canvas for argument mapping

This guide shows you how to arrange claim notes spatially in an Obsidian Canvas to find the argument structure before drafting.

## When to use it

Open a canvas when you have 8–15 relevant claim notes on a topic and need to see how they fit together before writing. Below 8 notes the argument isn't ready; above 15, split into sections and do one at a time.

## Steps

**1. Create the canvas file**

In `40-workbench/<project>/03-canvas/`, create a new Obsidian Canvas file. Name it after the chapter or argument section: `chapter-2-receptivity-argument.canvas`.

**2. Collect the notes**

Drag the relevant claim notes from the file explorer onto the canvas. Include paper-notes for key sources if helpful, but primarily use claim notes — they already state the argument in your words.

**3. Arrange spatially**

Group notes by sub-argument. Place notes that support the same claim together. Draw arrows to show logical flow: premise → implication → conclusion. Use text cards (no wikilink) for transitional claims that aren't in any note yet — these are gaps.

**4. Identify gaps**

Any text card that points to an empty space is a gap. A claim you've written on the canvas but haven't grounded in a claim note is an unverified assertion. Before drafting, either find a claim note that supports it, or write one from a source.

**5. Build the outline**

Once the spatial arrangement is stable, write an outline directly from the canvas groupings. Each group becomes a section; the notes within a group become the evidence for that section's claim.

Save the outline as `40-workbench/<project>/02-framing/CHOSEN.md` (or extend an existing framing document).

**6. Draft**

Open the canvas in a split pane. Draft section by section from the outline, citing citekeys from the claim notes visible on the canvas. You should never be improvising claims in the draft — every substantive claim in the prose should correspond to a claim note on the canvas.

## Conventions

- One canvas per argument cluster or chapter section, not one per paper
- Archive the canvas when the section is complete: set `lifecycle: archived` on the canvas note
- Canvas files live in `40-workbench/<project>/03-canvas/` — the agent's search scope excludes this folder (canvas files are not queryable by Dataview)
- Never embed a canvas in a draft note — canvas format does not export to Pandoc

## When a canvas gap can't be filled

If a text card can't be grounded in a claim note, either soften the outline claim or queue the missing source via `Cmd+P → Memoria: capture source from URL`. See [How to find new sources](../sources/find-new-sources.md) for the full candidate triage flow.

---

## Related

- Drafting from a committed outline: [How to draft with the Writer](draft-with-writer.md)
- Producing the outline the canvas maps: [How to frame a writing project](frame-a-project.md)
- Triage candidates for gaps the canvas exposes: [How to find new sources](../sources/find-new-sources.md)
- Why claim notes (not canvas cards) are the knowledge unit: [Note body structure](../../explanation/knowledge/note-body-structure.md)
