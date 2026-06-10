---
title: "Analyze claims"
type: pattern
lifecycle: current
posture: peer-reviewer
mode: both
action: analyze
input: selection-or-note
output_target: "projects/"
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
