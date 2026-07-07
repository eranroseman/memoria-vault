---
title: Integrity link target check
type: operation
description: Check that typed note links target checked current Concepts.
operation_id: integrity-link-target-check
allowed_tools:
- integrity_checker
allowed_paths:
- digests/
- fulltexts/
- notes/
- hubs/
- projects/
- .memoria/journal/
allowed_network: []
prompt_version: integrity-link-target-check.v1
io_schema:
  input: checked_notes
  output: link_findings
risk_class: low
required_checks: []
tags:
- alpha11
- integrity
id: operations/integrity-link-target-check
links: {}
---

# Operation

Flag checked note links whose targets are missing, unchecked, or stale.
