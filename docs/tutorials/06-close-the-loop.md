---
title: "Tutorial 06: Close the loop"
parent: Tutorials
nav_order: 6
---

# Tutorial 06: Close the loop

Memoria is useful only if work returns to a visible, reviewable state. This
tutorial closes requests, refreshes projections, and commits the workspace.

## Steps

**1. Inspect active requests and attention.**

```bash
memoria request list --workspace .
memoria attention list --workspace .
memoria attention worklist --workspace .
```

Requests are operation state. Attention items are PI-facing work. They are
different surfaces over the same control plane.

**2. Resolve attention items you have handled.**

```bash
memoria attention resolve --workspace . <attention-path> --apply --reason "Handled"
```

Use `--reject` or `--defer` when that is the true disposition.

**3. Refresh projections before you commit.**

```bash
memoria workspace scan --workspace .
memoria workspace rebuild --workspace . --search
memoria status --workspace .
```

**4. Commit the vault state.**

```bash
git status --short
git add <changed-checked-files>
git commit -m "Update Memoria workspace"
```

Stage only the paths you intentionally changed. Do not commit raw provider
secrets or unrelated local files.

## What you should have seen

- Requests, attention, projections, and Git commits close different parts of the loop.
- The engine observes and checks direct edits before they become trusted read state.
- The durable handoff is the workspace commit, not the chat transcript.

Next: [Make it your own](07-make-it-your-own.md).
