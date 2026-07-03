---
title: Capture PDF source
type: operation
check_status: checked
description: Capture a supplied PDF blob as a checked catalog source.
operation_id: capture-pdf-source
allowed_tools:
- trusted_writer
allowed_paths:
- catalog/
- journal/
- references.bib
allowed_network: []
runner: pydantic-ai
model: deterministic-fixture
prompt_version: capture-pdf-source.v1
io_schema:
  input: pdf_blob
  output: checked_source
risk_class: medium
required_checks:
- memoria-runtime
tags:
- alpha11
- capture
id: operations/capture-pdf-source
standing: current
links: {}
---

# Operation

Store a PDF raw copy, extracted page text, and checked source metadata through
the worker.
