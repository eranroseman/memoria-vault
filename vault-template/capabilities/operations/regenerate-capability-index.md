---
title: Regenerate capability index
type: operation
check_status: checked
description: Regenerate the tracked capability index projection.
operation_id: regenerate-capability-index
allowed_tools:
- projection_writer
allowed_paths:
- capabilities/
- journal/
allowed_network: []
runner: pydantic-ai
model: deterministic-fixture
prompt_version: regenerate-capability-index.v1
io_schema:
  input: capability_concepts
  output: capability_index_projection
risk_class: low
required_checks:
- projection-drift
tags:
- alpha11
- projection
id: operations/regenerate-capability-index
standing: current
links: {}
---

# Operation

Render `capabilities/_generated/capability-index.json` from checked capability Concepts.
