---
title: The honesty card
parent: Kanban board
grand_parent: Explanation
nav_order: 2
---

# The honesty card

An Inbox card is the one artifact the PI is guaranteed to read, so its format is where automation bias is won or lost. Research is blunt about the failure mode: hand a human a confident verdict and their scrutiny drops. And for a *proposal*, the verdict is a **given** — the agent surfaced the item because it recommends it, so printing "recommend: ACCEPT" adds nothing and subtracts attention. The honesty card ([ADR-51](../../adr/51-inbox-category-and-honesty-card.md)) is the answer: **proposals carry an honest argument, not a verdict; verification cards lead with the finding.**

The card schemas live in `.memoria/schemas/types/` alongside every other type — a card is just an `inbox/` note on the universal lifecycle chain, validated by the same Linter pass. Engines and lanes (a lane is a background agent's execution path on the board — see [Glossary](../../reference/glossary.md)) share one card-writer, so every card of a given type is shaped identically.

---

## The three card shapes

| Shape | Types | Carries | Deliberately omits | Why |
| --- | --- | --- | --- | --- |
| Proposal | `candidate`, `gap` | `argument_against`, `certainty`, and the source/gap facts | Verdict | The card already implies "consider this"; the PI needs decision material, not a rubber stamp. |
| Verification | `flag`, `alert` | `finding` and `agent_recommendation` | Human disposal | The point is what the check found; even a `clean` flag closes nothing on its own. |
| Work prompt | `work-prompt` | The work waiting on the PI | Verdict | It is a review or worklist handle, not a proposal to accept. |

The generated field lists are in [Inbox card fields](../../reference/inbox-card-fields.md). `agent_recommendation` is a soft verdict only; [Board states and the review gate](states.md) owns the enum and the "never a gate" rule.

---

## Graded loudness

`loudness` decides where a card appears:

| Loudness | Surface |
| --- | --- |
| `quiet`, `notice` | Pull-only. |
| `alert` | Push-worthy. |
| `block` | Push-worthy and pauses delegation / review-gated promotion until resolved. |

The 30-minute test is owned by [Interaction channels](../architecture/human-channels.md): does this change what the PI should do in the next 30 minutes?

---

## What deliberately isn't a card

| Not a card | Why |
| --- | --- |
| Classification | It is audited, correctable metadata; gating it would be a rubber stamp ([ADR-54](../../adr/54-two-decision-kinds-batch-worklists.md)). |
| High-cardinality screening | It becomes a Bases-backed worklist plus one aggregate work-prompt, not dozens of cards. |
| `review-request` | Any card awaiting the PI is simply in `proposed`, pointing at the artifact under review. |

---

## Related

- Conceptual overview: [Kanban board](README.md)
- State machine: [Board states and the review gate](states.md)
- The decision-kind model the card serves: [Why promotion is gated](../knowledge/promotion-model.md)
- The card types in the type system: [Document types and epistemic roles](../knowledge/document-types.md)
- How policy gates writes: [Policy MCP](../../reference/policy-mcp.md)
