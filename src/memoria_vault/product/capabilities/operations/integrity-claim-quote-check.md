---
title: Integrity claim quote check
type: operation
description: Check whether a claim's quoted evidence appears in its source.
operation_id: integrity-claim-quote-check
allowed_tools:
- integrity_checker
allowed_paths:
- catalog/
- digests/
- fulltexts/
- notes/
- hubs/
- projects/
- .memoria/journal/
allowed_network: []
prompt_version: integrity-claim-quote-check.v1
io_schema:
  input: checked_concepts
  output: integrity_findings
risk_class: low
required_checks: []
tags:
- alpha11
- integrity
id: operations/integrity-claim-quote-check
links: {}
---

# Operation

Flag checked claims whose quote cannot be found in the referenced source text.
