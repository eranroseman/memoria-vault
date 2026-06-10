---
title: "Extract claim stubs"
type: pattern
lifecycle: current
posture: librarian
mode: library
action: extract
input: source-note
output_target: "notes/fleeting/"
model_hint: ""
version: "1.0"
adapted_from: "fabric/extract_wisdom"
created: 2026-06-10
---

# Pattern

From the source note in {{input}}, draft candidate claim stubs: one atomic,
source-grounded assertion per stub, each a single sentence with the citekey and the
locating detail (section/figure/page) that grounds it. Stubs marked "rewrite required"
— the PI distills the claim in their own words; never copy the author's phrasing.
