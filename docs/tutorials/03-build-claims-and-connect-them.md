---
title: "Tutorial 03: Build notes and connect them"
parent: Tutorials
nav_order: 3
---

# Tutorial 03: Build notes and connect them

In this lesson, you will create two atomic notes, check them, and add one typed
link between them.

## Steps

**1. Write one atomic claim-bearing note.**

```bash
memoria new note "JITAI receptivity varies by burden" \
  --workspace . \
  --mode claim \
  --tag jitai \
  --body "JITAI receptivity depends partly on current participant burden."
```

Save the created note path from the command output.
Notice that the path is under `notes/`.

**2. Write a second note that can relate to it.**

```bash
memoria new note "Burden is partly contextual" \
  --workspace . \
  --mode claim \
  --tag jitai \
  --body "Burden changes with context, recent prompts, and task demands."
```
Save this note path too. The link command needs both paths.

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
- `check_status` is runtime state, not frontmatter.
- Typed links make notes usable as a graph.

Next: [Draft a section from your notes](04-draft-a-section-from-your-claims.md).
