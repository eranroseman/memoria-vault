---
title: The honesty card
parent: Kanban board
nav_order: 2
---

# The honesty card

An Inbox card is the one artifact the PI is guaranteed to read, so its format is where automation bias is won or lost. Research is blunt about the failure mode: hand a human a confident verdict and their scrutiny drops. And for a *proposal*, the verdict is a **given** — the agent surfaced the item because it recommends it, so printing "recommend: ACCEPT" adds nothing and subtracts attention. The honesty card ([ADR-51](../../adr/51-inbox-category-and-honesty-card.md)) is the answer: **proposals carry an honest argument, not a verdict; verification cards lead with the finding.**

The card schemas live in `.memoria/schemas/types/` alongside every other type — a card is just an `inbox/` note on the universal lifecycle chain, validated by the same Linter pass. Engines and lanes (a lane is a background agent's execution path on the board — see [Glossary](../../reference/glossary.md)) share one card-writer, so every card of a given type is shaped identically.

---

## Proposal cards: candidate and gap

A `candidate` (a *found* source proposed for intake) and a `gap` (a *missing*-source need) are approval-gate items (the gate is the human approval step — see [Glossary](../../reference/glossary.md)). There is **no verdict field** — the verdict is implied by the card existing. `argument_against` and `certainty` are what make the PI judge the argument rather than wave through a foregone conclusion. A card whose against-case is vacuous is a badly written card, and the design rule applies: *an Inbox item a human can clear without reading is a design smell* — give it real decision material or automate the decision. The full field list is in [Inbox card fields](../../reference/inbox-card-fields.md#proposal-cards).

## Verification cards: flag and alert

A `flag` (a verification or integrity issue) and an `alert` (a drift or retraction notice) are different: here the verdict is *not* a given — the whole point is what the check found. So these cards are **finding-first**: `finding` leads the card, and `agent_recommendation` carries the verdict the proposal cards deliberately omit. The full field list is in [Inbox card fields](../../reference/inbox-card-fields.md#verification-cards). `agent_recommendation` — the soft, agent-set verdict whose 3-tier enum and never-a-gate rule are defined in [Board states and the review gate](states.md) — is meaningful here precisely because it is *not* implied; still, a `clean` flag closes nothing on its own.

## Work prompts: work-prompt

A `work-prompt` is the third shape: not a proposal to judge and not a finding to adjudicate, but **work waiting on the PI** — the board export raises one when a worker card reaches `done`, and a batch worklist surfaces as one aggregate prompt. Like proposals, it carries **no verdict**; see [Inbox card fields](../../reference/inbox-card-fields.md#work-prompts).

---

## Graded loudness

Every card can carry a `loudness` level, and each level has a defined outcome — the difference between an ambient signal and an interruption is a design decision, not a worker's mood. `quiet` and `notice` stay pull-only; `alert` and `block` are push-worthy; an open `block` card also pauses delegation and review-gated promotion (writes that need PI approval — see [Glossary](../../reference/glossary.md)) until the PI resolves it. The four levels and the 30-minute test that picks a card's surface (*does it change what the PI does in the next 30 minutes?*) are owned by [Interaction channels](../architecture/human-channels.md).

---

## What deliberately isn't a card

**Classification** ships as audited, correctable metadata — a gate on it would be a rubber stamp ([ADR-54](../../adr/54-two-decision-kinds-batch-worklists.md)). **High-cardinality screening** (a coverage report with dozens of keep/reject calls) becomes a Bases-backed batch worklist plus *one* aggregate work-prompt card — never N cards, which would flood a queue meant to converge to zero and train select-all-accept. And there is no `review-request` type: any card awaiting the PI is simply in `proposed`, pointing at the artifact under review.

---

## Related

- Conceptual overview: [Kanban board](README.md)
- State machine: [Board states and the review gate](states.md)
- The decision-kind model the card serves: [Why promotion is gated](../knowledge/promotion-model.md)
- The card types in the type system: [Document types and epistemic roles](../knowledge/document-types.md)
- How policy gates writes: [Policy MCP](../../reference/policy-mcp.md)
