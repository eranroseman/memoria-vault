---
title: "Render project argument canvas"
type: operation
check_status: checked
description: "Render a checked project argument graph as an Obsidian Canvas projection."
operation_id: render-project-argument-canvas
allowed_tools:
  - projection_writer
allowed_paths:
  - knowledge/
  - journal/
allowed_network: []
runner: local
model: deterministic-fixture
prompt_version: render-project-argument-canvas.v1
io_schema:
  input: checked_project
  output: argument_canvas
risk_class: low
required_checks:
  - projection-drift
tags: [alpha11, canvas]
---

# Operation

Render `argument.canvas` from checked project thesis links.
