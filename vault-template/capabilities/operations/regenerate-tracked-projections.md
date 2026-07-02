---
title: Regenerate tracked projections
type: operation
check_status: checked
description: Regenerate all tracked generated workspace projections.
operation_id: regenerate-tracked-projections
allowed_tools:
- projection_writer
allowed_paths:
- index.md
- catalog/
- knowledge/
- capabilities/
- references.bib
- journal/
allowed_network: []
runner: pydantic-ai
model: deterministic-fixture
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
standing: current
links: {}
---

# Operation

Render `index.md`, bundle indexes, `knowledge/_views/index.md`, `references.bib`,
and `capabilities/_generated/capability-index.json`.
