---
title: "Acknowledge attention"
type: operation
check_status: checked
description: "Record that the PI acknowledged a generated attention item."
operation_id: acknowledge-attention
allowed_tools:
  - trusted_writer
allowed_paths:
  - journal/
  - .memoria/index/
allowed_network: []
runner: local
model: deterministic-fixture
prompt_version: acknowledge-attention.v1
io_schema:
  input: attention_target
  output: resolved_event
risk_class: low
required_checks: []
tags: [alpha11, attention]
---

# Operation

Resolve a generated attention item as acknowledged through the worker journal.
