---
title: Capture BibTeX source
type: operation
description: Stage one BibTeX record as an unchecked catalog Work seed.
operation_id: capture-bibtex-source
allowed_tools:
- trusted_writer
allowed_paths:
- .memoria/blobs/source-content/
- .memoria/journal/
allowed_network: []
prompt_version: capture-bibtex-source.v1
io_schema:
  input: bibtex_record
  output: unchecked_work_seed
risk_class: medium
required_checks:
- memoria-runtime
tags:
- alpha16
- capture
id: operations/capture-bibtex-source
links: {}
---

# Operation

Parse a BibTeX record, write durable source-content blobs, stage an unchecked
SQLite catalog row, and queue DOI enrichment when a DOI is present. The
operation does not create source/entity markdown or update `bibliography.bib`.
