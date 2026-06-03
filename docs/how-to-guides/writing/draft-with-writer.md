---
title: Draft with the Writer
parent: Writing
nav_order: 6
---


# Draft with the Writer

Use the Writer profile to generate outline proposals, draft prose, and suggest structural organization. Drafting is human-led — the Writer assists with phrasing and linking, but the argument assembly is yours.

## Prerequisites

- A writing project scaffolded with a corpus map ([Start a writing project](start-a-writing-project.md))
- At least one framing chosen — either from a Writer `counter-outline` session or written by hand in `02-framing/CHOSEN.md`
- The Writer profile installed

## Steps

**1. Optionally, generate competing framings first.**

If you haven't committed to a structure yet:

```bash
hermes -p memoria-writer chat -s draft
# then, in the session:
/counter-outline "question: <your research question>" \
  --context 40-workbench/<project>/01-map/corpus-map.md
```

The Writer generates 2–3 competing argument structures. Save the one you choose to `02-framing/CHOSEN.md`.

**2. For section-length work (8–15 claims), arrange on Canvas before drafting.**

Create a new `.canvas` file in `40-workbench/<project>/03-canvas/`. Drag claim notes from the file explorer onto the canvas. Group them by sub-argument, draw arrows for logical flow. Identify any gap (a text card pointing to an empty space) as a missing claim or source that needs work before drafting.

**3. Start the drafting session.**

Open the Writer profile:

```bash
hermes -p memoria-writer chat -s draft
```

**4. Draft section by section.**

Provide the Writer with your outline and relevant claim notes as context:

```bash
/draft "write an introduction for: <section topic>" \
  --context 40-workbench/<project>/02-framing/CHOSEN.md \
  --context 30-synthesis/01-claims/<claim1>.md \
  --context 30-synthesis/01-claims/<claim2>.md
```

Write the resulting prose into `40-workbench/<project>/04-drafts/<section>.md`. Cite citekeys in-text (`[@mamykina2010sense]`). Edit freely — the Writer's output is a starting point.

**5. Do not draft past unsupported claims.**

If your outline includes a claim with no backing in your claim notes, stop and either find the source or acknowledge the gap. The Verifier will flag it on commit regardless — it's faster to address it now.

**6. Commit each section as you finish it.**

Committing triggers the Verify hook, which checks all citations and flags unsupported claims:

```bash
git add 40-workbench/<project>/04-drafts/<section>.md
git commit -m "draft: <section name>"
```

Read the `[!verification]` callout at the top of the draft file after each commit.

## Verify

- Each committed draft section has a `[!verification]` callout at the top
- The callout shows `status: clean` or lists specific gaps to address
- The Canvas file (if used) is saved to `03-canvas/` and not embedded in any draft

## Related

- Previous step: [Start a writing project](start-a-writing-project.md)
- Next step: [Verify and revise a draft](verify-and-revise.md)
- Canvas sub-workflow: [Use canvas for argument mapping](use-canvas-for-argument-mapping.md)
- Conceptual background on the Writer: [The Writer](../../explanation/profiles/writer.md)
