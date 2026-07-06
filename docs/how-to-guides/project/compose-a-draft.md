---
title: Compose a draft
parent: Project
grand_parent: How-to guides
nav_order: 2
---

# Compose a draft

Use the project WRITE loop when checked notes are ready to become prose.

```bash
memoria project slice --workspace <vault> projects/<project>/project.md --query "<topic>"
```

Edit `projects/<project>/outline.md` in your editor. The list order is the
draft order; typed links stay on the notes themselves.

```bash
memoria project compose --workspace <vault> projects/<project>/project.md
memoria project verify --workspace <vault> projects/<project>/project.md
```

If verification reports an evidence item that you accept or reject after review,
record that disposition:

```bash
memoria project resolve-evidence --workspace <vault> projects/<project>/project.md \
  --evidence-id ev-1234abcd \
  --decision accept \
  --reason "Reviewed source span"
```

If a passage should become durable knowledge:

```bash
memoria project promote --workspace <vault> projects/<project>/project.md \
  --title "Atomic note title" \
  --passage "Exact draft passage"
```

The promoted note is unchecked until reviewed.
