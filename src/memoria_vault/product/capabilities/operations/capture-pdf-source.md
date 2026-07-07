---
title: Capture PDF source
type: operation
description: Capture a supplied PDF blob as a catalog Work row.
operation_id: capture-pdf-source
allowed_tools:
- trusted_writer
allowed_paths:
- .memoria/blobs/source-content/
- .memoria/journal/
allowed_network: []
prompt_version: capture-pdf-source.v1
io_schema:
  input: pdf_blob
  output: catalog_work_row
risk_class: medium
required_checks:
- memoria-runtime
tags:
- alpha11
- capture
id: operations/capture-pdf-source
links: {}
---

# Operation

Store a PDF raw copy and extracted page text as an unchecked catalog Work row
plus source-content blobs through the worker.
