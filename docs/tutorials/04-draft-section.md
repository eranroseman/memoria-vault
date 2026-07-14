---
title: "04: Draft section"
parent: Tutorials
nav_order: 4
---

# 04: Draft section

Project drafting starts from checked notes, not from chat history. The project
slice proposes membership; the PI edits the outline; then compose and verify run
through project operations.

## Steps

**1. Create a project Concept.**

```bash
memoria new project "Tutorial project" \
  --workspace . \
  --description "A small project for learning the project WRITE loop."
```

Save the created project path.
Notice that the path is under `projects/`.

**2. Check the project before checked-read operations use it.**

```bash
memoria check --workspace . <project-path>
```

New Concepts start unchecked. The slice operation reads only checked project
and note state.

**3. Propose a slice.**

```bash
memoria project slice --workspace . <project-path> --query "jitai receptivity"
```

The slice writes `projects/<project>/outline.md`. It is a proposal, not a final
argument map.
Notice the outline path printed by the command.

**4. Edit the outline.**

Open the outline and keep only the notes that belong in the draft. The line
order is the draft order.
For this tutorial, keep the two checked notes from Tutorial 03 and put the
receptivity note first.

**5. Compose and verify.**

```bash
memoria project compose --workspace . <project-path>
memoria project verify --workspace . <project-path>
```

Verification reports evidence markers, missing support, and review-required
items. Treat those as work to resolve before export.
Notice the draft path and the verification output. The next lesson will create
one explicit review item and resolve it.

## What you should have seen

- The outline is the PI-controlled bridge from notes to prose.
- Draft composition is repeatable from checked project state.
- Verification is a gate before export, not an afterthought.

Next: [05: Verify evidence](05-verify-evidence.md).
