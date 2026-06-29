---
title: "Capture source"
type: operation
check_status: checked
description: "Capture supplied source metadata and text as a checked catalog source."
operation_id: capture-source
allowed_tools:
  - trusted_writer
allowed_paths:
  - catalog/
  - journal/
  - references.bib
allowed_network: []
runner: local
model: deterministic-fixture
prompt_version: capture-source.v1
io_schema:
  input: source_payload
  output: checked_source
risk_class: medium
required_checks:
  - memoria-profile
tags: [alpha11, capture]
---

# Operation

Write a checked source Concept, extracted content, raw copy, and entity Concepts.
