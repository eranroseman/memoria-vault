---
title: "Capture Zotero source"
type: operation
check_status: checked
description: "Stage one exported Zotero item as an unchecked catalog Work seed."
operation_id: capture-zotero-source
allowed_tools:
  - trusted_writer
allowed_paths:
  - .memoria/blobs/source-content/
  - journal/
allowed_network: []
runner: local
model: deterministic-fixture
prompt_version: capture-zotero-source.v1
io_schema:
  input: exported_zotero_item
  output: unchecked_work_seed
risk_class: medium
required_checks:
  - memoria-runtime
tags: [alpha14, capture, zotero]
---

# Operation

Parse one exported Zotero item object, write durable source-content blobs, stage
an unchecked SQLite catalog row, and queue DOI enrichment when a DOI is present.
The operation does not fetch from a live Zotero API, create source/entity
Markdown, or update `references.bib`.
