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

**1. Use the tutorial project you framed in Tutorial 01.**

The project already exists — you framed it at the end of
[01: System tour](01-system-tour.md), and it has been aiming discovery
ever since. Recover its path if you did not save it:

```bash
memoria list --workspace . --type project --json
```

Save the project path.
Notice that the path is under `projects/`, and that the WRITE loop reuses
the framed project instead of creating a new one.

**2. Check the project before checked-read operations use it.**

```bash
memoria check --workspace . <project-path>
```

Like every new Concept, the project started unchecked when Tutorial 01
created it. The slice operation reads only checked project and note state.

**3. Propose a slice.**

```bash
memoria project slice --workspace . <project-path> --query "jitai receptivity"
```

The slice writes `projects/<project>/outline.md`. It is a proposal, not a final
argument map.
Notice the outline path printed by the command.

**4. Edit the outline.**

Open `projects/<project>/outline.md`. The slice matched the two checked notes
from Tutorial 03 — the only notes in this vault. Keep both note lines and
order them so the receptivity note ("JITAI receptivity varies by burden") is
first and the burden note second. The line order is the draft order.
Notice that the outline holds exactly those two note lines, receptivity first.

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

For more detail: [Project slice, outline, draft composition, verification, and
write-back](../how-to-guides/project/compose-a-draft.md).

Next: [05: Verify evidence](05-verify-evidence.md).
