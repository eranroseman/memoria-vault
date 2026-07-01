---
title: "Export project"
type: operation
check_status: checked
description: "Export a checked project composition to Markdown or a Pandoc-backed format."
operation_id: export-project
allowed_tools:
  - projection_writer
allowed_paths:
  - knowledge/
  - references.bib
allowed_network: []
runner: pydantic-ai
model: deterministic-fixture
prompt_version: export-project.v1
io_schema:
  input: checked_project
  output: project_export
risk_class: low
required_checks: []
tags: [alpha14, project, export]
---

# Operation

Render a checked project, its argument state, and available references as a deterministic export artifact.
