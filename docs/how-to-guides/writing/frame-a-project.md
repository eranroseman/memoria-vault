---
title: How to frame a writing project
parent: Writing
---


# How to frame a writing project

Generate 2–3 competing argument structures, optionally run a lens reading through the Socratic profile, and commit to one framing before drafting. This prevents the first outline from winning by default.

## Prerequisites

- A corpus map exists for this project ([How to assess your corpus for a project](assess-your-corpus.md))
- The Writer and Socratic profiles are installed

## Steps

**1. Run `counter-outline` to generate competing framings.**

```bash
hermes -p memoria-writer chat -s counter-outline
# then, in the session:
/counter-outline --project <project-slug>
```

The Writer generates 2–3 alternative outlines, each foregrounding a different structure (e.g., chronological vs. mechanism-of-action vs. theoretical-lens). Outputs land in `40-workbench/<project-slug>/02-framing/` as `option-A.md`, `option-B.md`, `option-C.md`.

**2. Read each option.**

Open the framing options in Obsidian. Don't commit immediately — let them sit for at least an hour. The framing that feels obvious after a break is usually the right one.

**3. Optionally, run a lens reading with the Socratic profile.**

If you want to stress-test one of the framings through a specific theoretical lens:

```bash
hermes -p memoria-socratic chat -s lens-reading
# then, in the session:
/lens <lens-name> --project <project-slug>
```

Examples: `/lens equity --project jitai-receptivity-review` or `/lens ecological-validity --project jitai-receptivity-review`.

The Socratic profile is write-denied — its outputs appear in the ACP pane only. Copy or paraphrase anything useful into a new `02-framing/lens-notes.md` file manually.

**4. Choose a framing and write `CHOSEN.md`.**

Create `40-workbench/<project-slug>/02-framing/CHOSEN.md` with:
- The selected outline (copy from one of the options, edit freely)
- 2–3 sentences explaining why you chose this framing over the alternatives

The `CHOSEN.md` file is required before the project card can advance to drafting. An empty or one-line `CHOSEN.md` is not a valid framing decision.

## Verify

- `40-workbench/<project-slug>/02-framing/CHOSEN.md` exists with an outline and a rationale
- The project card has advanced beyond `framing` on the Kanban board

## Related

- Previous step: [Assess your corpus](assess-your-corpus.md)
- Next step: [Draft with the Writer](draft-with-writer.md)
- Socratic lens-reading and write-denial: [The Socratic](../../explanation/profiles/socratic.md)
- The Writer's counter-outline: [The Writer](../../explanation/profiles/writer.md)
