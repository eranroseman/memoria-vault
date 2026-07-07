---
title: Capture URL source
type: operation
description: Fetch a URL snapshot and stage it as a catalog Work row.
operation_id: capture-url-source
allowed_tools:
- trusted_writer
allowed_paths:
- .memoria/blobs/source-content/
- .memoria/journal/
allowed_network:
- http://
- https://
prompt_version: capture-url-source.v1
io_schema:
  input: url
  output: catalog_work_row
risk_class: medium
required_checks:
- memoria-runtime
tags:
- alpha11
- capture
id: operations/capture-url-source
links: {}
---

# Operation

Fetch a source URL and stage the snapshot as an unchecked catalog Work row plus
source-content blobs.
