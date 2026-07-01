---
title: "Analyze claims"
type: operation
check_status: checked
description: "Extract and rank truth claims from selected input."
operation_id: analyze-claims
allowed_tools:
  - trusted_writer
allowed_paths:
  - catalog/
  - knowledge/
allowed_network: []
runner: pydantic-ai
model: deterministic-fixture
prompt_version: analyze-claims.v1
io_schema:
  input: selection_or_note
  output: claim_analysis
risk_class: medium
required_checks:
  - memoria-profile
posture: peer-reviewer
mode: both
action: analyze
input: selection-or-note
output_target: ".memoria/staging/knowledge/"
model_hint: ""
version: "1.0"
adapted_from: "fabric/analyze_claims"
created: 2026-06-10
---

# Pattern

Extract every distinct truth claim in {{input}}. For each: state the claim in one
sentence; rate the evidence given (none / weak / specific); list what is cited for it;
give the strongest counter-consideration in the text or an explicit "[none offered]".
End with the three claims most worth verifying first, with one line on why each.
