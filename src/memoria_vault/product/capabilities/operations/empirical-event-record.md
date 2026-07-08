---
title: Record empirical event
type: operation
description: Validate and append one empirical-use event to the journal.
operation_id: empirical-event-record
allowed_tools:
- trusted_writer
allowed_paths:
- .memoria/journal/
- .memoria/index/
allowed_network: []
prompt_version: empirical-event-record.v1
io_schema:
  input: empirical_event.v1
  output: journal_event_ref.v1
risk_class: low
required_checks: []
tags:
- empirical-use
id: operations/empirical-event-record
links: {}
---

# Operation

Validate a strict empirical-use event payload and store it as an append-only journal event.
