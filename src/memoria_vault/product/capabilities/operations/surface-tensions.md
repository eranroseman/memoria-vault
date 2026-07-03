---
title: Surface tensions
type: operation
check_status: checked
description: List Tier-1/Tier-2 contradiction candidates across checked notes without writing links.
operation_id: surface-tensions
allowed_tools:
- read_checked_concepts
- trusted_writer
allowed_paths:
- catalog/
- inbox/
- knowledge/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: surface-tensions.v1
io_schema:
  input: checked_workspace
  output: tension_candidates
risk_class: medium
required_checks:
- memoria-runtime
version: '1.0'
adapted_from: open-notebook/transformations
created: 2026-06-10
id: operations/surface-tensions
standing: current
links: {}
---

# Pattern

Across checked notes and works, list candidate tensions: pairs that cannot both be
fully right. Tier-1 must pass the HANS-style high-overlap/opposite-meaning gate
before it may classify candidates. Tier-2 runs only on Tier-1 abstain cases or
degraded hard cases, must return grounded quotes from both checked texts, and
otherwise abstains. Every candidate routes to PI review through attention. Never
write the `contradicts` link.
