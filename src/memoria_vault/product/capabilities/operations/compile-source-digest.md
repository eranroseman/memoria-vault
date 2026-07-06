---
title: Compile source digest
type: operation
description: Compile a checked Work into a machine-owned digest, new hubs, and curated
  hub suggestions.
operation_id: compile-source-digest
allowed_tools:
- trusted_writer
allowed_paths:
- catalog/sources/
- .memoria/blobs/source-content/
- works/
- hubs/
allowed_network: []
prompt_version: compile-source-digest.v1
untrusted_fields:
- input
- source_text
- pi_interview_notes
io_schema:
  input: checked_work_id
  output: digest_plus_hubs_and_suggestions
risk_class: medium
required_checks:
- memoria-runtime
posture: co-pi
mode: knowledge
action: synthesize
input: checked-work
output_target: .memoria/staging/works/
version: '1.0'
created: 2026-06-29
id: operations/compile-source-digest
links: {}
---

# Pattern

From the checked Work identified by {{input}}, compile the per-source digest,
then compound hub updates. The digest and new hubs are machine-owned; curated hub
changes stay as suggestions.
