---
title: "Tutorial 04: Draft a section from your claims"
parent: Tutorials
nav_order: 4
---

# Tutorial 04: Draft a section from your claims

Use the project WRITE loop to turn checked notes into a draft section.

```bash
memoria project slice --workspace <vault> projects/<project>/project.md --query "<topic>"
```

Edit `projects/<project>/outline.md` so the checked note IDs are in the order
you want.

```bash
memoria project compose --workspace <vault> projects/<project>/project.md
memoria project verify --workspace <vault> projects/<project>/project.md
```

If verification reports unresolved evidence, fix the notes, edit the draft, or
record the PI disposition before exporting.
