---
title: "Capture URL source"
type: operation
check_status: checked
description: "Fetch a URL snapshot and capture it as a checked catalog source."
operation_id: capture-url-source
allowed_tools:
  - trusted_writer
allowed_paths:
  - catalog/
  - journal/
  - references.bib
allowed_network:
  - http://
  - https://
runner: local
model: deterministic-fixture
prompt_version: capture-url-source.v1
io_schema:
  input: url
  output: checked_source
risk_class: medium
required_checks:
  - memoria-runtime
tags: [alpha11, capture]
---

# Operation

Fetch a source URL and capture the snapshot through the trusted writer.
