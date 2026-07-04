---
title: Rebuild checked qmd source
type: operation
description: Rebuild qmd's disposable input tree from checked retrieval documents.
operation_id: rebuild-checked-qmd-source
allowed_tools:
- indexer
allowed_paths:
- catalog/
- knowledge/
- capabilities/
- .memoria/index/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: rebuild-checked-qmd-source.v1
io_schema:
  input: checked_workspace
  output: qmd_manifest
risk_class: low
required_checks: []
tags:
- alpha11
- index
id: operations/rebuild-checked-qmd-source
links: {}
---

# Operation

Refresh the checked-only qmd input tree and manifest from current checked
Concepts, checked Work text, compact citations, and graph-neighborhood
documents.
