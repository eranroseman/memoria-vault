---
title: Render project argument canvas
type: operation
description: Render a checked project argument graph as an Obsidian Canvas projection.
operation_id: render-project-argument-canvas
allowed_tools:
- projection_writer
allowed_paths:
- works/
- sources/
- notes/
- hubs/
- projects/
- journal/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: render-project-argument-canvas.v1
io_schema:
  input: checked_project
  output: argument_canvas
risk_class: low
required_checks:
- projection-drift
tags:
- alpha11
- canvas
id: operations/render-project-argument-canvas
links: {}
---

# Operation

Render `argument.canvas` from checked project thesis links.
