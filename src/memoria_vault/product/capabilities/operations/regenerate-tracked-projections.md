---
title: Regenerate tracked projections
type: operation
description: Regenerate tracked workspace and project Canvas projections.
operation_id: regenerate-tracked-projections
allowed_tools:
- projection_writer
allowed_paths:
- index.md
- bibliography.bib
- projects/
- .memoria/journal/
allowed_network: []
prompt_version: regenerate-tracked-projections.v1
io_schema:
  input: workspace
  output: tracked_projections
risk_class: low
required_checks:
- projection-drift
tags:
- alpha11
- projection
id: operations/regenerate-tracked-projections
links: {}
---

# Operation

Render `index.md`, `bibliography.bib`, and existing project `argument.canvas`
projections.
