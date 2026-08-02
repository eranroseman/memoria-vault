---
title: Record empirical event
type: operation
description: Validate and record one empirical-use event in the telemetry table.
operation_id: empirical-event-record
allowed_tools:
- trusted_writer
allowed_paths:
- .memoria/index/
allowed_network: []
prompt_version: empirical-event-record.v1
io_schema:
  input: empirical_event.v1
  output: telemetry_event_ref.v1
risk_class: low
required_checks: []
tags:
- empirical-use
id: operations/empirical-event-record
links: {}
---

# Operation

Validate a strict empirical-use event payload and store it as one analytics-only
`telemetry_events` row. Nothing here is hash-chained, git-visible, or read by a
gate or verifier.
