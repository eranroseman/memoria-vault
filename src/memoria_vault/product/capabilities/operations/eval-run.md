---
title: Run vault eval
type: operation
description: Plan the current vault-eval task set through the local runtime engine.
operation_id: eval-run
allowed_tools:
- eval_dispatch
allowed_paths:
- .memoria/eval/
allowed_network: []
prompt_version: eval-run.v1
io_schema:
  input: eval_run_request
  output: eval_run_plan
risk_class: low
required_checks:
- eval-task-schema
tags:
- alpha16
- eval
id: operations/eval-run
links: {}
---

# Operation

Read current `.memoria/eval/` eval-task fixtures, create local idempotent eval task
plans, and write `.memoria/eval/last-run.md` unless the request is a dry run.
