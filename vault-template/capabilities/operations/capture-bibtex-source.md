---
title: "Capture BibTeX source"
type: operation
check_status: checked
description: "Capture one BibTeX record as a checked catalog source."
operation_id: capture-bibtex-source
allowed_tools:
  - trusted_writer
allowed_paths:
  - catalog/
  - journal/
  - references.bib
allowed_network: []
runner: local
model: deterministic-fixture
prompt_version: capture-bibtex-source.v1
io_schema:
  input: bibtex_record
  output: checked_source
risk_class: medium
required_checks:
  - memoria-runtime
tags: [alpha11, capture]
---

# Operation

Parse a BibTeX record and write the source, content, raw copy, and references projection.
