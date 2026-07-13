---
title: The honesty prompt
parent: Request control plane
grand_parent: Execution
nav_order: 2
---

# The honesty prompt

An Inbox prompt is the one artifact the PI is guaranteed to read, so its format is where automation bias is won or lost. Research is blunt about the failure mode: hand a human a confident verdict and their scrutiny drops. And for a *proposal*, the verdict is a **given** — the agent surfaced the item because it recommends it, so printing "recommend: ACCEPT" adds nothing and subtracts attention. The honesty body ([checked means checks passed, not a human verdict](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)) is the answer: **proposals carry an honest argument, not a verdict; verification prompts lead with the finding.**

Inbox prompts are generated attention projections, not durable Concept types.
Operation-specific helpers currently write them in enrichment, knowledge,
integrity, and digest flows. They share frontmatter conventions, but there is no
single attention writer that guarantees identical shaping across every flow.

---

## The three prompt shapes

Attention prompts have three broad shapes. Proposals carry the case for and
against an action, plus uncertainty. Verification prompts lead with the finding
because the PI needs to inspect what the check found. Work prompts point to work
waiting on the PI. None of the three turns an automated recommendation into a
human disposition.

Machine recommendations are soft verdicts only; [Request states and the review
gate](states.md) owns the "never a gate" rule.

---

## Graded loudness

Loudness decides whether attention stays pull-only or becomes push-worthy. The
point is not notification decoration; it is preserving the PI's attention for
items that can change near-term work.

The 30-minute test is owned by [Architecture](../../architecture/README.md#interaction-channels): does this change what the PI should do in the next 30 minutes?

---

## What deliberately isn't an attention prompt

Routine classification, high-cardinality screening, and seeded-error probes do
not become verdict prompts. They are either metadata, worklists, or calibration
signals. Turning them into accept/reject prompts would create rubber-stamp work.

---

## Related

- Conceptual overview: [Request control plane](README.md)
- State machine: [Request states and the review gate](states.md)
- The decision-kind model the prompt serves: [Decision points](decision-points.md)
- The attention shapes in the type system: [Document types and epistemic roles](../../knowledge/document-types.md)
- How policy gates writes: [Policy gate](../../../reference/control-and-policy/policy-mcp.md)
