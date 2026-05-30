# `canvas` template

Argument map for chapter or section drafting. Lives in `40-workbench/*/03-canvas/`. Human-authored. Canvas files are `.canvas` (Obsidian format); the metadata sits in a companion frontmatter file or in the file's own front-matter block.

## Frontmatter

```yaml
---
title: ""
type: canvas
lifecycle: proposed        # proposed (draft) | current (frozen, once the draft it feeds is exported)
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
- Place claim notes and paper notes spatially; draw edges for support, contradiction, or causation.
- Keep one canvas per project or chapter; canvases are scratchpads, not deliverables.

## When to use

Open a canvas when you have 8–15 relevant claim notes on a topic and need to see how they fit together before writing. Not for exploration (use `hermes run draft`); for argument assembly.

See the Canvas → Draft sub-workflow for the full process.

## Archival

When the section drafted from a canvas is exported, archive the canvas with `lifecycle: archived`. Canvases have provenance value (they record the argument map) and should not be deleted.
