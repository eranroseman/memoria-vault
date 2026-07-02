---
title: Record Co-PI interview
type: operation
check_status: checked
description: Record one PI interview takeaway for a checked source.
operation_id: record-copi-interview
allowed_tools:
- trusted_writer
allowed_paths:
- catalog/sources/
- knowledge/projects/
- journal/
allowed_network: []
runner: pydantic-ai
model: deterministic-fixture
prompt_version: record-copi-interview.v1
io_schema:
  input: interview_turn
  output: copi_interview_event
risk_class: low
required_checks: []
tags:
- alpha11
- copi
id: operations/record-copi-interview
standing: current
links: {}
---

# Operation

Record a PI interview answer for later digest synthesis.
