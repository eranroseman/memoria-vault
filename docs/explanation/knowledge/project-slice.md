---
title: Project slice
parent: Knowledge
grand_parent: Explanation
nav_order: 7
---

# Project slice

A project slice is the checked-note set a project drafts from. Its canonical
file is `projects/<project>/outline.md`:

```text
- <note-ulid> — why this note belongs here
```

The ULID identifies the note. Line order is draft order. Connections are never
stored in the outline: Memoria recomputes them from each member note's
`links:` and shows only links where both endpoints are slice members.

`memoria project slice` proposes membership with BM25 only. The PI can edit the
outline directly.
