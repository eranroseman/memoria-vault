# `canvas` template

Argument map for chapter or section drafting. Lives in `40-workbench/04-canvas/`. Human-authored. Canvas files are `.canvas` (Obsidian format); the metadata sits in a companion frontmatter file or in the file's own front-matter block.

## Frontmatter

```yaml
---
title: ""
type: canvas
status: draft              # draft | frozen (frozen once the draft it feeds is exported)
purpose: ""
related_projects: []
related_notes: []
schema_version: 1
created:
updated:
---
```

## Structure

- A canvas is an argument map, not a canonical note.
- Place claim notes and source notes spatially; draw edges for support, contradiction, or causation.
- Keep one canvas per project or chapter; canvases are scratchpads, not deliverables.

## When to use

Open a canvas when you have 8–15 relevant claim notes on a topic and need to see how they fit together before writing. Not for exploration (use `hermes run draft`); for argument assembly.

See [`04-workflows.md`](../04-workflows.md) Canvas → Draft sub-workflow for the full process.

## Archival

When the section drafted from a canvas is exported, archive the canvas with `status: frozen`. Canvases have provenance value (they record the argument map) and should not be deleted.
