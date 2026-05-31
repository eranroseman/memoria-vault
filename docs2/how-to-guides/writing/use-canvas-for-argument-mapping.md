# Use canvas for argument mapping

**Goal:** Arrange 8–15 claim notes spatially to find the argument structure before drafting.

Canvas is the step between synthesis and writing. When you have enough claim notes on a topic but no clear sense of how they fit into an argument, open a canvas. Not for exploration — that's the Socratic ACP pane or a Mapper query. Canvas is for argument assembly: you already know what you think; now you are figuring out how to say it.

## When to use it

Open a canvas when you have 8–15 relevant claim notes on a topic and need to see how they fit together before writing. Below 8 notes the argument isn't ready; above 15, the canvas becomes hard to manage — split into sections and do one at a time.

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

## What a gap on the canvas means

A gap in the canvas argument structure is a gap in your research. You have two options:

1. **Soften the claim** in the outline — hedge it or remove it if it can't be grounded
2. **Add to the reading queue** — use `Cmd+P → Memoria: capture source from URL` to queue a paper that would ground the claim; the Librarian will bring it in

This is the same gap-closure loop the Verifier uses during citation checking. The canvas surfaces it visually before drafting; the Verifier surfaces it structurally after drafting.
