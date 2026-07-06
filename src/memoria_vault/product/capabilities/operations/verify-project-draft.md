---
title: Verify project draft
type: operation
description: Verify a composed project draft's evidence markers and structural refs.
operation_id: verify-project-draft
allowed_tools:
- projection_writer
allowed_paths:
- projects/
- notes/
- journal/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: verify-project-draft.v1
io_schema:
  input: project_draft
  output: verification_report
risk_class: low
required_checks: []
tags:
- alpha17
- project
- verification
id: operations/verify-project-draft
links: {}
---

# Operation

Rebuild evidence-set rows from draft markers and report unresolved or
review-required evidence before export.
