---
title: Regenerate capability index
type: operation
description: Regenerate the local packaged-capability index cache.
operation_id: regenerate-capability-index
allowed_tools:
- projection_writer
allowed_paths:
- .memoria/index/
- journal/
allowed_network: []
prompt_version: regenerate-capability-index.v1
io_schema:
  input: packaged_capability_manifests
  output: local_capability_index_cache
risk_class: low
required_checks:
- projection-drift
tags:
- alpha11
- projection
id: operations/regenerate-capability-index
links: {}
---

# Operation

Render `.memoria/index/capability-index.json` from packaged capability manifests.
