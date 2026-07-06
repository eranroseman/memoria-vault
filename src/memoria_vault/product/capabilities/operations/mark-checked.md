---
title: Mark checked
type: operation
description: Promote an observed PI edit back to checked after worker checks pass.
operation_id: mark-checked
allowed_tools:
- trusted_writer
allowed_paths:
- catalog/
- works/
- sources/
- notes/
- hubs/
- projects/
- capabilities/
- journal/
allowed_network: []
prompt_version: mark-checked.v1
io_schema:
  input: target_path
  output: check_event
risk_class: medium
required_checks:
- memoria-runtime
tags:
- alpha11
- trace
id: operations/mark-checked
links: {}
---

# Operation

Record a worker-owned DB/read API `check_status = checked` transition for an
observed PI edit.
