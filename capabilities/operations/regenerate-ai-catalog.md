---
title: "Regenerate ai-catalog"
type: operation
check_status: checked
description: "Regenerate the tracked capability catalog projection."
operation_id: regenerate-ai-catalog
allowed_tools:
  - projection_writer
allowed_paths:
  - capabilities/
  - journal/
allowed_network: []
runner: local
model: deterministic-fixture
prompt_version: regenerate-ai-catalog.v1
io_schema:
  input: capability_concepts
  output: ai_catalog_projection
risk_class: low
required_checks:
  - projection-drift
tags: [alpha11, projection]
---

# Operation

Render `capabilities/ai-catalog.json` from checked capability Concepts.
