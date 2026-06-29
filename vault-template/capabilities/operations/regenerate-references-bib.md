---
title: "Regenerate references.bib"
type: operation
check_status: checked
description: "Regenerate the tracked BibTeX projection from checked sources."
operation_id: regenerate-references-bib
allowed_tools:
  - projection_writer
allowed_paths:
  - catalog/
  - references.bib
  - journal/
allowed_network: []
runner: local
model: deterministic-fixture
prompt_version: regenerate-references-bib.v1
io_schema:
  input: checked_sources
  output: references_bib_projection
risk_class: low
required_checks:
  - projection-drift
tags: [alpha11, projection]
---

# Operation

Render `references.bib` from checked catalog sources.
