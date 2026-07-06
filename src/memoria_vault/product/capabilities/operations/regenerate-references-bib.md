---
title: Regenerate bibliography.bib
type: operation
description: Regenerate the tracked BibTeX projection from checked SQLite catalog
  rows.
operation_id: regenerate-references-bib
allowed_tools:
- projection_writer
allowed_paths:
- catalog/
- bibliography.bib
- journal/
allowed_network: []
prompt_version: regenerate-references-bib.v1
io_schema:
  input: checked_catalog_works
  output: bibliography_bib_projection
risk_class: low
required_checks:
- projection-drift
tags:
- alpha12
- projection
id: operations/regenerate-references-bib
links: {}
---

# Operation

Render `bibliography.bib` from checked SQLite catalog rows.
