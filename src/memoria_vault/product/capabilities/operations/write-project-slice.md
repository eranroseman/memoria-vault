---
title: Write project slice
type: operation
description: Propose a checked project note slice with BM25 and write its outline.
operation_id: write-project-slice
allowed_tools:
- projection_writer
allowed_paths:
- notes/
- projects/
- .memoria/journal/
allowed_network: []
prompt_version: write-project-slice.v1
io_schema:
  input: checked_project
  output: project_outline
risk_class: low
required_checks: []
tags:
- alpha17
- project
- outline
id: operations/write-project-slice
links: {}
---

# Operation

Write `outline.md` for a checked project from BM25-ranked checked notes.
