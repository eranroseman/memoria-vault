---
title: Capture source
type: operation
check_status: checked
description: Capture supplied source metadata and text; DOI/ISBN records stage for
  enrichment.
operation_id: capture-source
allowed_tools:
- trusted_writer
allowed_paths:
- .memoria/blobs/source-content/
- catalog/
- journal/
- references.bib
allowed_network: []
runner: pydantic-ai
model: deterministic-fixture
prompt_version: capture-source.v1
io_schema:
  input: source_payload
  output: checked_source
risk_class: medium
required_checks:
- memoria-runtime
tags:
- alpha11
- capture
id: operations/capture-source
standing: current
links: {}
---

# Operation

Write supplied source content into the catalog path. Scholarly DOI/ISBN inputs
are staged in SQLite and `.memoria/blobs/source-content/` for later enrichment;
portable file/text inputs write a catalog DB row plus immutable blob payloads.
