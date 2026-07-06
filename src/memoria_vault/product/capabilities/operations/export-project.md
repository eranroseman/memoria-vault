---
title: Export project
type: operation
description: Export a checked project composition to Markdown or a Pandoc-backed format.
operation_id: export-project
allowed_tools:
- projection_writer
allowed_paths:
- projects/
- notes/
- hubs/
- bibliography.bib
allowed_network: []
prompt_version: export-project.v1
io_schema:
  input: checked_project
  output: project_export
risk_class: low
required_checks: []
tags:
- alpha16
- project
- export
id: operations/export-project
links: {}
---

# Operation

Render a checked project, its argument state, and available references as a deterministic export artifact.
