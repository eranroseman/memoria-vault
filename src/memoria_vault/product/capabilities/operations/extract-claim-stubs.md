---
title: Extract claim stubs
type: operation
check_status: checked
description: Draft source-grounded candidate note stubs from checked Work text.
operation_id: extract-claim-stubs
allowed_tools:
- trusted_writer
allowed_paths:
- catalog/
- knowledge/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: extract-claim-stubs.v1
io_schema:
  input: checked_work
  output: note_candidates
risk_class: medium
required_checks:
- memoria-runtime
posture: librarian
mode: library
action: extract
input: checked-work
output_target: .memoria/staging/knowledge/
model_hint: ''
version: '1.0'
adapted_from: fabric/extract_wisdom
created: 2026-06-10
id: operations/extract-claim-stubs
standing: current
links: {}
---

# Pattern

From the checked Work text in {{input}}, draft candidate claim stubs: one
atomic, source-grounded assertion per stub, each a single sentence with the
citekey and the locating detail (section/figure/page) that grounds it. Stubs
marked "rewrite required" -- the PI distills the claim in their own words; never
copy the author's phrasing.
