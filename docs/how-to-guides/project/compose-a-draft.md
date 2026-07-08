---
title: Compose a draft
parent: Project
grand_parent: How-to guides
nav_order: 2
---

# Compose a draft

Use the project WRITE loop when checked notes are ready to become prose.

## Prerequisites

- A checked Project under `projects/`
- Checked notes that belong in the project argument
- Typed links or clear evidence relationships among the notes

## Steps

**1. Propose the project slice.**

```bash
memoria project slice --workspace <vault> projects/<project>/project.md --query "<topic>"
```

The command writes `projects/<project>/outline.md`.

**2. Edit the outline.**

Keep only the notes that belong in the draft. The list order is the draft order;
typed links stay on the notes themselves.

**3. Compose and verify the draft.**

```bash
memoria project compose --workspace <vault> projects/<project>/project.md
memoria project verify --workspace <vault> projects/<project>/project.md
```

## Resolve evidence review

If verification reports an evidence item that you accept or reject after review,
record that disposition:

```bash
memoria project resolve-evidence --workspace <vault> projects/<project>/project.md \
  --evidence-id ev-1234abcd \
  --decision accept \
  --reason "Reviewed source span"
```

Then edit the draft or source notes and run verification again.

## Promote reusable prose

If a passage should become durable knowledge:

```bash
memoria project promote --workspace <vault> projects/<project>/project.md \
  --title "Atomic note title" \
  --passage "Exact draft passage"
```

The promoted note is unchecked until reviewed.

## Verify

- `projects/<project>/outline.md` contains the intended checked notes.
- `projects/<project>/draft.md` exists.
- `memoria project verify` reports no unresolved evidence item you still need to handle.
