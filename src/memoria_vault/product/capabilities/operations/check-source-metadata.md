---
title: Check source metadata
type: operation
description: Run bibliographic metadata checks over checked catalog Works.
operation_id: check-source-metadata
allowed_tools:
- integrity_checker
allowed_paths:
- catalog/
- inbox/
- .memoria/journal/
allowed_network: []
prompt_version: check-source-metadata.v1
io_schema:
  input: checked_catalog_works
  output: metadata_findings
risk_class: low
required_checks: []
tags:
- alpha11
- integrity
id: operations/check-source-metadata
links: {}
---

# Operation

Inspect checked catalog Work metadata, including exact duplicate source external IDs,
deterministic title/year/first-author duplicate blocks, and duplicate person
ORCID/OpenAlex IDs or entity-name blocks, and emit shadow or routed findings.
Active record-linkage findings surface stable `inbox/` work prompts for PI
review; the operation never merges records.
