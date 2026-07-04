---
title: Run vault eval
type: operation
check_status: checked
description: Plan the current vault-eval task set through the local runtime engine.
operation_id: eval-run
allowed_tools:
- eval_dispatch
allowed_paths:
- system/eval/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: eval-run.v1
io_schema:
  input: eval_run_request
  output: eval_run_plan
risk_class: low
required_checks:
- eval-task-schema
tags:
- alpha15
- eval
id: operations/eval-run
standing: current
links: {}
---

# Operation

Read checked `system/eval/` task Concepts, create local idempotent eval task
plans, and write `system/eval/last-run.md` unless the request is a dry run.
