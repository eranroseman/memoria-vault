---
title: Frame paper
type: operation
check_status: checked
description: Record PI-supplied paper framing fields on a project.
operation_id: frame-paper
allowed_tools:
- trusted_writer
allowed_paths:
- knowledge/projects/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: frame-paper.v1
io_schema:
  input: paper_frame
  output: unchecked_project
risk_class: low
required_checks: []
tags:
- alpha15
- project
id: operations/frame-paper
standing: current
links: {}
---

# Operation

Record the target, audience, question, contribution, gap, claim-evidence map,
figure plan, and limitations that make a project draftable.
