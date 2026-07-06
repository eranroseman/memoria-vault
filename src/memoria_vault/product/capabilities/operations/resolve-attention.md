---
title: Resolve attention
type: operation
description: Record that the PI resolved or dismissed a generated attention item.
operation_id: resolve-attention
allowed_tools:
- trusted_writer
allowed_paths:
- journal/
- .memoria/index/
allowed_network: []
prompt_version: resolve-attention.v1
io_schema:
  input: attention_target
  output: resolved_event
risk_class: low
required_checks: []
tags:
- alpha11
- attention
id: operations/resolve-attention
links: {}
---

# Operation

Resolve or dismiss a generated attention item through the worker journal.
