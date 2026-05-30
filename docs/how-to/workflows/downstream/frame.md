---
topic: workflows
---

# Frame

**Group.** Downstream (stage workflow)
**Goal.** Generate 2–3 competing project framings *before* committing to one. Prevents "first outline wins by default."

## Pipeline position

Between [Assess](assess.md) and outline (inside [Write](write.md)).

## Steps

1. With `corpus-map.md` in hand from [Assess](assess.md), the human moves the project card to `framing`.
2. Writer claims it with the `counter-outline` skill loaded. The skill's policy denies writes to `30-synthesis/**` and `50-deliverables/**`; outputs land only in `40-workbench/<project>/02-framing/`.
3. Writer generates 2–3 alternative project outlines, each prioritizing a different framing (chronological / mechanism-of-action / stakeholder-perspective / theoretical-lens). Files are named `framing/option-A.md`, `option-B.md`, `option-C.md`.
4. Optionally, the human switches to the **Socratic profile** and runs the `lens-reading` command with one or more named lenses (e.g., `mamykina-lens`, `veinot-equity-lens`) to read the corpus through a specific theoretical frame. Because Socratic is write-denied, lens readings don't appear as files — they appear as ACP conversation outputs the human can copy (or summarize by hand) into `framing/lens-mamykina.md` while in Writer profile.
5. The human compares the framings, picks one (or synthesizes across them), and commits the decision by creating `40-workbench/<project>/02-framing/CHOSEN.md` with the selected outline and a brief rationale.
6. The card moves to `outlining` (continues into [Write](write.md)).

## Owners

Writer executes `counter-outline` (scratch-only by construction). Socratic executes `lens-reading` (write-denied; outputs are conversational, captured by the human). Human owns the framing choice.

## Commands

- `hermes -p memoria-writer run counter-outline --project <project-name>` for the outlines
- `hermes -p memoria-socratic chat --command lens-reading --lens <lens-name> --project <project-name>` for the lens readings

## Why this is a stage and not a pattern inside Write

Without a stage, framing exploration is silently optional — humans who are time-pressed skip it and default to their first instinct. With a stage, every project card has to pass through `framing` (with a `CHOSEN.md` artifact) before drafting can begin. The architectural constraint isn't enforceable (the human could write a one-line CHOSEN.md and call it done), but the board signal is enforceable enough — a project sitting in `framing` for weeks is the diagnostic.

## Related

- **Profiles:** [profiles/writer.md](../../../explanation/profiles/writer.md), [profiles/socratic.md](../../../explanation/profiles/socratic.md)
- **Restrictive skill:** `counter-outline` — see [profiles/README.md restrictive skills](../../../explanation/profiles/README.md#skills-with-restrictive-policy)
- **Previous workflow:** [Assess](assess.md)
- **Umbrella workflow:** [Write](write.md)
