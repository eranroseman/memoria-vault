---
title: Apply decision-rule notices
type: operation
description: Record every pre-registered decision rule that crossed its threshold as
  one notice card and one armed-to-fired status flip.
operation_id: apply-decision-rule-notices
allowed_tools:
- trusted_writer
allowed_paths:
- inbox/
- .memoria/config/
- .memoria/journal/
allowed_network: []
prompt_version: apply-decision-rule-notices.v1
io_schema:
  input: assembled_dashboard_panels
  output: decision_rule_notices
risk_class: low
required_checks: []
tags:
- i1
- decision-rules
id: operations/apply-decision-rule-notices
links: {}
---

# Operation

Recompute the dashboard panels and the decision-rule assessment from the
workspace, then record each crossing: one deduped `notice` card and one `armed`
to `fired` flip in `.memoria/config/decision-rules.yaml`. Assessment is a read
and stays a read; this is the only path that applies one. The rule still only
recommends — nothing here acts on the recommendation.
