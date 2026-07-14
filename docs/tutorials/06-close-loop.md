---
title: "06: Close loop"
parent: Tutorials
nav_order: 6
---

# 06: Close loop

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
Notice whether the rejected evidence item from Tutorial 05 still appears.

**2. Resolve attention items you have handled.**

```bash
memoria attention resolve --workspace . <attention-path> --apply --reason "Handled"
```

Use `--reject` or `--defer` when that is the true disposition.
If there are no attention items, continue. An empty queue is a successful
result in this tutorial.

**3. Refresh projections before you commit.**

```bash
memoria workspace scan --workspace .
memoria workspace rebuild --workspace . --search
memoria journal verify --workspace .
memoria status --workspace .
```
Notice that `status` reports the refreshed workspace after the scan and
rebuild, and that `journal verify` is the one authoritative trust-read path:
it hash-chain-verifies the event journal and its head anchor before you rely
on anything the refreshed projections reported.

**4. Back up state that Git does not track.**

```bash
memoria workspace backup --workspace . ../memoria-backup
```

`.memoria/memoria.sqlite`, `.memoria/blobs/`, and `.memoria/journal/` are
gitignored, so the catalog rows, source blobs, and event journal never reach
the commit in the next step. `workspace backup` is what makes that state
durable, and `memoria workspace restore <dir>` (add `--force` to overwrite a
live workspace) is how you bring it back. `doctor bundle` from Tutorial 01
fails this same check when blobs exist with no valid backup.

**5. Commit the vault state.**

```bash
git status --short
git add <changed-checked-files>
git commit -m "Update Memoria workspace"
```

Stage only the paths you intentionally changed. Do not commit raw provider
secrets or unrelated local files.
For this tutorial, seeing the intentional changed paths in `git status --short`
is enough; commit only when you are ready to keep the sample workspace.

## What you should have seen

- Requests, attention, projections, and Git commits close different parts of the loop.
- The engine observes and checks direct edits before they become trusted read state.
- The durable handoff is the workspace commit for checked files, plus a
  `workspace backup` for the catalog, blobs, and journal state Git ignores —
  not the chat transcript.

For more detail: [Back up and restore the workspace](../how-to-guides/operate/back-up-and-restore-the-workspace.md).

Next: [07: Customize](07-customize.md).
