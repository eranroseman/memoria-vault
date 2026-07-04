---
title: Capture BibTeX source
type: operation
check_status: checked
description: Stage one BibTeX record as an unchecked catalog Work seed.
operation_id: capture-bibtex-source
allowed_tools:
- trusted_writer
allowed_paths:
- .memoria/blobs/source-content/
- journal/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: capture-bibtex-source.v1
io_schema:
  input: bibtex_record
  output: unchecked_work_seed
risk_class: medium
required_checks:
- memoria-runtime
tags:
- alpha15
- capture
id: operations/capture-bibtex-source
standing: current
links: {}
---

# Operation

Parse a BibTeX record, write durable source-content blobs, stage an unchecked
SQLite catalog row, and queue DOI enrichment when a DOI is present. The
operation does not create source/entity markdown or update `references.bib`.
