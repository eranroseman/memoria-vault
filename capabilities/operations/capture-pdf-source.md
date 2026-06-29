---
title: "Capture PDF source"
type: operation
check_status: checked
description: "Capture a supplied PDF blob as a checked catalog source."
operation_id: capture-pdf-source
allowed_tools:
  - trusted_writer
allowed_paths:
  - catalog/
  - journal/
  - references.bib
allowed_network: []
runner: local
model: deterministic-fixture
prompt_version: capture-pdf-source.v1
io_schema:
  input: pdf_blob
  output: checked_source_with_annotation_refs
risk_class: medium
required_checks:
  - memoria-profile
tags: [alpha11, capture]
---

# Operation

Store a PDF raw copy and checked source metadata through the worker.
