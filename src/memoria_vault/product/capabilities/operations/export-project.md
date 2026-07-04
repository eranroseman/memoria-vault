---
title: Export project
type: operation
check_status: checked
description: Export a checked project composition to Markdown or a Pandoc-backed format.
operation_id: export-project
allowed_tools:
- projection_writer
allowed_paths:
- knowledge/
- references.bib
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: export-project.v1
io_schema:
  input: checked_project
  output: project_export
risk_class: low
required_checks: []
tags:
- alpha15
- project
- export
id: operations/export-project
standing: current
links: {}
---

# Operation

Render a checked project, its argument state, and available references as a deterministic export artifact.
