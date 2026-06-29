---
title: "Resolve attention"
type: operation
check_status: checked
description: "Record that the PI resolved a generated attention item."
operation_id: resolve-attention
allowed_tools:
  - trusted_writer
allowed_paths:
  - journal/
  - .memoria/index/
allowed_network: []
runner: local
model: deterministic-fixture
prompt_version: resolve-attention.v1
io_schema:
  input: attention_target
  output: resolved_event
risk_class: low
required_checks: []
tags: [alpha11, attention]
---

# Operation

Resolve a generated attention item through the worker journal.
