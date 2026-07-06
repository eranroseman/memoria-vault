---
title: Compose project draft
type: operation
description: Compose a project draft from outline-ordered checked notes.
operation_id: compose-project-draft
allowed_tools:
- projection_writer
allowed_paths:
- notes/
- projects/
- journal/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: compose-project-draft.v1
io_schema:
  input: project_outline
  output: project_draft
risk_class: low
required_checks: []
tags:
- alpha17
- project
- draft
id: operations/compose-project-draft
links: {}
---

# Operation

Write `draft.md` for a checked project from the current `outline.md`, carrying
inline evidence-set markers for each drafted section.
