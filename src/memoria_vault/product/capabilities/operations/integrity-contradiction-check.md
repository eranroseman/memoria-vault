---
title: Integrity contradiction check
type: operation
description: Surface explicit contradiction markers as integrity findings.
operation_id: integrity-contradiction-check
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
prompt_version: integrity-contradiction-check.v1
io_schema:
  input: checked_notes
  output: contradiction_findings
risk_class: low
required_checks: []
tags:
- alpha11
- integrity
id: operations/integrity-contradiction-check
links: {}
---

# Operation

Report checked notes that carry contradiction markers for PI review.
