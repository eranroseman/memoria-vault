---
title: "Capture Zotero source"
type: operation
check_status: checked
description: "Capture a Zotero item or Zotero Local API item key as a checked source."
operation_id: capture-zotero-source
allowed_tools:
  - trusted_writer
allowed_paths:
  - catalog/
  - journal/
  - references.bib
allowed_network:
  - http://localhost:23119/
  - http://127.0.0.1:23119/
runner: local
model: deterministic-fixture
prompt_version: capture-zotero-source.v1
io_schema:
  input: zotero_item
  output: checked_source
risk_class: medium
required_checks:
  - memoria-runtime
tags: [alpha11, capture, zotero]
---

# Operation

Import Zotero item metadata through the worker-owned capture path.
