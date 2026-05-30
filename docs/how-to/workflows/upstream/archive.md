---
topic: workflows
---

# Archive

**Group.** Upstream
**Goal.** Preserve superseded material instead of deleting it.

## Steps

1. Human marks a note `deprecated`, `superseded`, or `archived`.
2. Adds `superseded_by` if needed.
3. Moves the file to `95-archive/`.
4. The note drops out of active queries but remains in Git history.

## Owners

Human only. Hermes never autonomously archives.

## Commands

No CLI command — performed directly in the vault or via the Obsidian interface.

## Example

A 2019 reference page on JITAI timing is superseded by a fresher synthesis → the human sets `lifecycle: archived`, adds `superseded_by: [[jitai-timing-2024]]`, and moves the file to `95-archive/`. It drops out of active Dataview queries but stays in Git history and remains linkable, so older drafts that cite it don't break.

## Related

- **Anti-pattern:** treating archive as delete. Archived notes are preserved for traceability — see [Anti-patterns in workflows/README.md](../README.md#anti-patterns).
