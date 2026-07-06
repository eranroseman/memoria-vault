---
title: Capture source
type: operation
description: Capture supplied source metadata and text; DOI/ISBN records stage for
  enrichment.
operation_id: capture-source
allowed_tools:
- trusted_writer
allowed_paths:
- .memoria/blobs/source-content/
- journal/
allowed_network: []
prompt_version: capture-source.v1
io_schema:
  input: source_payload
  output: catalog_work_row
risk_class: medium
required_checks:
- memoria-runtime
tags:
- alpha11
- capture
id: operations/capture-source
links: {}
---

# Operation

Write supplied source content into a SQLite catalog Work row plus immutable
`.memoria/blobs/source-content/` payloads. Scholarly DOI/ISBN inputs are staged
for later enrichment; portable file/text inputs use the same catalog/blob path.
