---
title: Regenerate indexes
type: operation
check_status: checked
description: Regenerate tracked workspace and bundle index projections.
operation_id: regenerate-indexes
allowed_tools:
- projection_writer
allowed_paths:
- index.md
- catalog/
- knowledge/
- capabilities/
- journal/
allowed_network: []
runner: pydantic-ai
model: deterministic-fixture
prompt_version: regenerate-indexes.v1
io_schema:
  input: checked_concepts
  output: index_projections
risk_class: low
required_checks:
- projection-drift
tags:
- alpha11
- projection
id: operations/regenerate-indexes
standing: current
links: {}
---

# Operation

Render root and bundle `index.md` files from checked Concepts.
