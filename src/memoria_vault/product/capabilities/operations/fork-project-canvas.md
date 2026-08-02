---
title: Fork project canvas
type: operation
description: Copy a generated project argument canvas to an editable scratch canvas.
operation_id: fork-project-canvas
allowed_tools:
- trusted_writer
allowed_paths:
- projects/
- .memoria/journal/
allowed_network: []
prompt_version: fork-project-canvas.v1
io_schema:
  input: checked_project
  output: scratch_canvas
risk_class: low
required_checks:
- memoria-runtime
tags:
- alpha23
- canvas
id: operations/fork-project-canvas
links: {}
---

# Operation

Copy `argument.canvas` to `scratch-<name>.canvas` as an editable,
non-authoritative fork. The scratch canvas is not a tracked projection and is
never regenerated; a fork staleness read diffs it against the moving source
graph, and hand-drawn edges graduate through `curate-note-link`.
