---
title: Record Co-PI interview
type: operation
description: Record one PI interview takeaway for a checked source.
operation_id: record-copi-interview
allowed_tools:
- trusted_writer
allowed_paths:
- catalog/sources/
- projects/
- journal/
allowed_network: []
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
links: {}
---

# Operation

Record a PI interview answer for later digest synthesis.
