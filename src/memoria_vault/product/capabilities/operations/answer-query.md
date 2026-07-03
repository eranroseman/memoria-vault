---
title: Answer query
type: operation
check_status: checked
description: Answer an Ask query over checked retrieval documents with BM25 sources.
operation_id: answer-query
allowed_tools:
- read_checked_index
allowed_paths:
- catalog/
- knowledge/
- .memoria/index/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: answer-query.v1
io_schema:
  input: query
  output: sourced_answer_contract
risk_class: low
required_checks: []
tags:
- alpha11
- ask
id: operations/answer-query
standing: current
links: {}
---

# Operation

Return sources, unknowns, staleness, and contradictions for a checked-only query
over current Concepts, checked Work text, and graph-neighborhood documents.
