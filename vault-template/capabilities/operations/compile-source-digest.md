---
title: Compile source digest
type: operation
check_status: checked
description: Compile a checked source into a machine-owned digest, new hubs, and curated
  hub suggestions.
operation_id: compile-source-digest
allowed_tools:
- trusted_writer
allowed_paths:
- catalog/sources/
- .memoria/blobs/source-content/
- knowledge/digests/
- knowledge/hubs/
allowed_network: []
runner: pydantic-ai
model: deterministic-fixture
prompt_version: compile-source-digest.v1
io_schema:
  input: checked_source_id
  output: digest_plus_hubs_and_suggestions
risk_class: medium
required_checks:
- memoria-runtime
posture: co-pi
mode: knowledge
action: synthesize
input: checked-source
output_target: .memoria/staging/knowledge/
version: '1.0'
created: 2026-06-29
id: operations/compile-source-digest
standing: current
links: {}
---

# Pattern

From the checked source identified by {{input}}, compile the per-source digest,
then compound hub updates. The digest and new hubs are machine-owned; curated
hub changes stay as suggestions.
