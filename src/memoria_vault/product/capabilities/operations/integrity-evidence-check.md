---
title: Integrity evidence check
type: operation
description: Check that note evidence references resolve through checked catalog Works.
operation_id: integrity-evidence-check
allowed_tools:
- integrity_checker
allowed_paths:
- catalog/
- digests/
- fulltext/
- notes/
- hubs/
- projects/
- .memoria/journal/
allowed_network: []
prompt_version: integrity-evidence-check.v1
io_schema:
  input: checked_concepts
  output: integrity_findings
risk_class: low
required_checks: []
tags:
- alpha11
- integrity
id: operations/integrity-evidence-check
links: {}
---

# Operation

Flag evidence sets that do not resolve through the checked read barrier.
