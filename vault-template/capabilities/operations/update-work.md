---
title: Update Work
type: operation
check_status: checked
description: Apply PI-owned Work metadata and lifecycle updates through the worker
  queue.
operation_id: update-work
allowed_tools:
- trusted_writer
allowed_paths:
- journal/
allowed_network: []
runner: pydantic-ai
model: deterministic-fixture
prompt_version: update-work.v1
io_schema:
  input: work_update
  output: updated_work
risk_class: medium
required_checks:
- memoria-runtime
tags:
- alpha14
- catalog
id: operations/update-work
standing: current
links: {}
---

# Operation

Update one SQLite catalog Work row from explicit PI input, then journal the
metadata, standing, and classification changes. The operation does not write
source/entity Markdown or bypass the checked read barrier.
