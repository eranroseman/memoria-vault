---
title: "03: Connect notes"
parent: Tutorials
nav_order: 3
---

# 03: Connect notes

In this lesson, you will create two atomic notes, tie the first one to the
source Work from Tutorial 02, check them, and add one typed link between them.

## Steps

**1. Write one atomic claim-bearing note, tied to its source.**

```bash
memoria new note "JITAI receptivity varies by burden" \
  --workspace . \
  --mode claim \
  --tag jitai \
  --work-id <work-id> \
  --body "JITAI receptivity depends partly on current participant burden."
```

Replace `<work-id>` with the `work_id` you saved in Tutorial 02: the note
records the source Work the claim came from. Save the created note path from
the command output.
Notice that the path is under `notes/`.

**2. Write a second note that can relate to it.**

```bash
memoria new note "Burden is partly contextual" \
  --workspace . \
  --mode claim \
  --tag jitai \
  --body "Burden changes with context, recent prompts, and task demands."
```
This note is your own synthesis rather than a reading of the captured source,
so it takes no `--work-id`. Save this note path too. The link command needs
both paths.

**3. Check or repair the notes.**

```bash
memoria workspace scan --workspace .
memoria check --workspace . <first-note-path>
memoria check --workspace . <second-note-path>
```

Unchecked notes can exist, but checked-read surfaces use checked material.
After each `check`, the note should be available to checked-read operations.

**4. Curate a typed link.**

```bash
memoria link --workspace . \
  <second-note-path> \
  <first-note-path> \
  --rel supports \
  --reason "Contextual burden is one mechanism for variable receptivity."
```

Links are authored graph structure. They are different from search results or
similarity suggestions because the PI chooses the relationship.
Notice that the link is directional: the contextual-burden note supports the
receptivity note.

## What you should have seen

- Notes are the durable synthesis unit.
- A note can record the source Work it derives from, so claims trace back to
  captured sources.
- `check_status` is runtime state, not frontmatter.
- Typed links make notes usable as a graph.

For more detail: [Link checked notes](../how-to-guides/knowledge/link-checked-notes.md).

Next: [04: Draft section](04-draft-section.md).
