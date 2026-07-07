---
title: "Tutorial 03: Build notes and connect them"
parent: Tutorials
nav_order: 3
---

# Tutorial 03: Build notes and connect them

Alpha.19 has one durable `note` type. A note can carry `mode: claim`, but there
is no separate `claim` document type.

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

**2. Write a second note that can relate to it.**

```bash
memoria new note "Burden is partly contextual" \
  --workspace . \
  --mode claim \
  --tag jitai \
  --body "Burden changes with context, recent prompts, and task demands."
```

**3. Check or repair the notes.**

```bash
memoria workspace scan --workspace .
memoria check --workspace . <first-note-path>
memoria check --workspace . <second-note-path>
```

Unchecked notes can exist, but checked-read surfaces use checked material.

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

## What you should have seen

- Notes are the durable synthesis unit.
- `check_status` is runtime state, not frontmatter.
- Typed links make notes usable as a graph.

Next: [Draft a section from your notes](04-draft-a-section-from-your-claims.md).
