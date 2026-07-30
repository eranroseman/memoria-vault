---
title: Capture remote PDF source
type: operation
description: Fetch an allowlisted remote PDF and stage it as a catalog Work row.
operation_id: capture-remote-pdf-source
allowed_tools:
- trusted_writer
allowed_paths:
- .memoria/blobs/source-content/
- .memoria/journal/
allowed_network:
- https://www.ncbi.nlm.nih.gov/pmc/utils/oa/
- https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_pdf/
- https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_package/
- https://www.frontiersin.org/articles/
- https://aclanthology.org/
- https://sociologica.unibo.it/article/download/
- https://export.arxiv.org/pdf/
prompt_version: capture-remote-pdf-source.v1
io_schema:
  input: remote_pdf_descriptor
  output: catalog_work_row
risk_class: medium
required_checks:
- memoria-runtime
tags:
- alpha21
- capture
- import
id: operations/capture-remote-pdf-source
links: {}
---

# Operation

Fetch one resolver-supported PDF only after the worker has applied this
operation's finite network policy, then stage its bytes through the existing
local-PDF capture seam as an unchecked catalog Work row.
