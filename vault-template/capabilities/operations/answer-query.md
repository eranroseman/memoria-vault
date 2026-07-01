---
title: "Answer query"
type: operation
check_status: checked
description: "Answer an Ask query over checked retrieval documents with BM25 sources."
operation_id: answer-query
allowed_tools:
  - read_checked_index
allowed_paths:
  - catalog/
  - knowledge/
  - .memoria/index/
allowed_network: []
runner: pydantic-ai
model: deterministic-fixture
prompt_version: answer-query.v1
io_schema:
  input: query
  output: sourced_answer_contract
risk_class: low
required_checks: []
tags: [alpha11, ask]
---

# Operation

Return sources, unknowns, staleness, and contradictions for a checked-only query
over current Concepts, checked Work text, and graph-neighborhood documents.
