---
topic: workflows
---

# Write

**Group.** Downstream
**Goal.** Turn synthesized knowledge into chapters, papers, or other drafts. This workflow is the **umbrella** for the downstream pipeline — [Assess](assess.md), [Frame](frame.md), [Verify](verify.md), [Revise](revise.md), and [Export](export.md) each own one stage; this workflow ties them together and owns the outline / draft middle.

## Steps (mapped to downstream stages)

1. **Assess.** Run [Assess](assess.md) to produce `corpus-map.md`. Decide if the project is ready to write or needs more reading.
2. **Frame.** Run [Frame](frame.md) to generate 2–3 competing framings; commit to one in `framing/CHOSEN.md`.
3. **Arrange** *(optional)*. For chapter-sized work (8–15 claim notes), use Canvas to arrange the claims spatially. See Canvas → Draft sub-workflow below.
4. **Outline.** Derive heading scaffold from `framing/CHOSEN.md` (and Canvas groupings if used).
5. **Draft.** Write prose in `40-workbench/<project>/04-drafts/` with citekeys. Superseded claim notes (`superseded_by`) are excluded from the drafting context by default, and [Verify](verify.md) flags any that slip into a draft — see [ADR-22](../../../project/decisions/22-claim-supersession.md). Commit triggers the verify hook ([Verify](verify.md)).
6. **Verify.** [Verify](verify.md) fires automatically on draft commit. Read the `[!verification]` callout at the top of the draft.
7. **Revise.** [Revise](revise.md) closes the gap-loop. Loop back to step 5 until verify returns clean (or remaining gaps are accepted-soft).
8. **Export.** Run [Export](export.md) — Pandoc produces the deliverable in `50-deliverables/`.

## Owners

Human owns argument assembly and drafting (steps 3–5, 7). Mapper owns step 1 via `scope-project`. Writer with `counter-outline` owns step 2 (framing — and Socratic with `lens-reading` for lens-based framings); Verifier owns step 6 (verify); [Export](export.md) owns step 8. The middle (outline, draft) is human-led with Hermes assistance.

## Canvas → Draft sub-workflow

Canvas is the spatial layer between synthesis and writing. It is an argument map, not a canonical note. Use it when there are **8–15 relevant claim notes** to see how they fit together before drafting.

**1. Collect notes onto the canvas.** Drag claim notes from the file explorer onto a new Canvas file. Save as `40-workbench/<project>/03-canvas/{chapter-or-section-name}.canvas`.

**2. Arrange spatially.** Group notes by sub-argument. Place notes that support the same claim together. Draw arrows showing logical flow: claim → evidence → implication. Use text cards for transitional claims that aren't yet in any note.

**3. Identify gaps.** Any text card that points to an empty space is a gap. A claim with no supporting note needs either a new paper note or a new claim note before drafting starts. **Do not draft past unsupported claims.**

**4. Build the outline.** Once the spatial arrangement is stable, write the outline directly from Canvas groupings. Either by hand or:

```bash
hermes -p memoria-writer chat -s draft
# then, in the session:
/draft "outline the argument on {canvas topic}" \
  --context 30-synthesis/01-claims/{note1}.md \
  --context 30-synthesis/01-claims/{note2}.md
```

**5. Move to draft.** Create `40-workbench/<project>/04-drafts/{chapter-name}.md`. Open Canvas in a split pane. Write section by section, citing citekeys from notes on the Canvas.

**6. Archive the Canvas.** When the section is drafted, move the canvas to `95-archive/` with `lifecycle: archived`. Canvases are scratchpads, not deliverables — but they have provenance value (the argument map that was built).

**Conventions:**

- One Canvas per chapter section or argument cluster, not one per paper.
- Never embed a Canvas in a draft note — `.canvas` files don't export to Pandoc.
- Canvases live in `40-workbench/*/03-canvas/` while active; archived when frozen.

## Related

- **Stages owned elsewhere:** [Assess](assess.md), [Frame](frame.md), [Verify](verify.md), [Revise](revise.md), [Export](export.md)
- **Profile:** [profiles/writer.md](../../../explanation/profiles/writer.md)
- **Workspace layout:** [obsidian-ui/workspaces.md — Drafting workspace](../../../reference/obsidian-ui/workspaces.md)
