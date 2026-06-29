---
title: "Mark checked"
type: operation
check_status: checked
description: "Promote an observed PI edit back to checked after worker checks pass."
operation_id: mark-checked
allowed_tools:
  - trusted_writer
allowed_paths:
  - catalog/
  - knowledge/
  - capabilities/
  - journal/
allowed_network: []
runner: local
model: deterministic-fixture
prompt_version: mark-checked.v1
io_schema:
  input: target_path
  output: check_event
risk_class: medium
required_checks:
  - memoria-profile
tags: [alpha11, trace]
---

# Operation

Record a worker-owned `check_status: checked` transition for an observed PI edit.
