---
title: Regenerate tracked projections
type: operation
description: Regenerate all tracked generated workspace projections.
operation_id: regenerate-tracked-projections
allowed_tools:
- projection_writer
allowed_paths:
- index.md
- bibliography.bib
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

Render `index.md` and `bibliography.bib`.
