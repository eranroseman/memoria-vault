---
title: Rebuild checked search index
type: operation
description: Rebuild the checked-only BM25 search input tree and manifest.
operation_id: rebuild-checked-search-index
allowed_tools:
- indexer
allowed_paths:
- catalog/
- works/
- sources/
- notes/
- hubs/
- projects/
- capabilities/
- .memoria/index/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: rebuild-checked-search-index.v1
io_schema:
  input: checked_workspace
  output: search_manifest
risk_class: low
required_checks: []
tags:
- alpha11
- index
id: operations/rebuild-checked-search-index
links: {}
---

# Operation

Refresh the checked-only search input tree and manifest from current checked
Concepts, checked Work text, compact citations, and graph-neighborhood
documents.
