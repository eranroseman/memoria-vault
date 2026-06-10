---
title: The honesty card
parent: Kanban board
nav_order: 2
---

# The honesty card

An Inbox card is the one artifact the PI is guaranteed to read, so its format is where automation bias is won or lost. Research is blunt about the failure mode: hand a human a confident verdict and their scrutiny drops. And for a *proposal*, the verdict is a **given** — the agent surfaced the item because it recommends it, so printing "recommend: ACCEPT" adds nothing and subtracts attention. The honesty card ([ADR-51](../../adr/51-inbox-category-and-honesty-card.md), D49) is the answer: **proposals carry an honest argument, not a verdict; verification cards lead with the finding.**

The card schemas live in `.memoria/schemas/types/` alongside every other type — a card is just an `inbox/` note on the universal lifecycle chain, validated by the same Linter pass. Engines and lanes share one card-writer, so every card of a given type is shaped identically.

---

## Proposal cards: candidate and gap

A `candidate` (a *found* source proposed for intake) and a `gap` (a *missing*-source need) are approval-gate items. Their required fields (see [the candidate schema](../../../src/.memoria/schemas/types/candidate.yaml) and [the gap schema](../../../src/.memoria/schemas/types/gap.yaml)):

| Field              | What it carries                                              |
| ------------------ | ------------------------------------------------------------ |
| `title`            | the headline                                                 |
| `action`           | what you would be *accepting* if you act                     |
| `argument_for`     | the case for                                                 |
| `argument_against` | the agent's strongest honest self-rebuttal                   |
| `what_tipped_it`   | the single deciding reason                                   |
| `certainty`        | `confident` / `likely` / `unsure` — 3-level, action-labelled |
| `lifecycle`        | `proposed` (awaiting you) → `current` → `archived`           |

There is **no verdict field** — the verdict is implied by the card existing. The `argument_against` and `certainty` are the information-bearing fields: they are what make the PI judge the argument rather than wave through a foregone conclusion. A card whose against-case is vacuous is a badly written card, and the design rule applies: *an Inbox item a human can clear without reading is a design smell* — give it real decision material or automate the decision.

Optional fields carry provenance and routing: `citekey`/`url` (candidate), `raised_by`, `created`, and `loudness`.

## Verification cards: flag and alert

A `flag` (a verification or integrity issue) and an `alert` (a drift or retraction notice) are different: here the verdict is *not* a given — the whole point is what the check found. So these cards are **finding-first** (see [the flag schema](../../../src/.memoria/schemas/types/flag.yaml) and [the alert schema](../../../src/.memoria/schemas/types/alert.yaml)):

| Field                  | What it carries                                                      |
| ---------------------- | -------------------------------------------------------------------- |
| `title`                | the headline                                                         |
| `finding`              | what the check found — leads the card                                 |
| `agent_recommendation` | `inconclusive` / `issues-found` / `clean` (required on `flag`)        |
| `target` / `citekey`   | what is being flagged — a `flag` must point at something              |
| `lifecycle`            | `proposed` → `current` → `archived`                                   |

`agent_recommendation` is the soft 3-tier verdict ([ADR-50](../../adr/50-universal-lifecycle-and-maturity.md)) — meaningful here precisely because it is *not* implied, and still never a gate: a `clean` flag closes nothing on its own.

---

## Graded loudness

Every card can carry a `loudness` level, and each level has a defined outcome — the difference between an ambient signal and an interruption is a design decision, not a worker's mood:

| Level    | Outcome                                                                  |
| -------- | ------------------------------------------------------------------------ |
| `quiet`  | logged only; aggregated in the weekly review; no interruption            |
| `notice` | appears in the relevant dashboard + weekly review; no push               |
| `alert`  | appears in Home's "what needs me"; pushed; does **not** block            |
| `block`  | blocks the action (dispatch / promotion) until acknowledged; pushed      |

The test for push vs dashboard: *does it change what the PI does in the next 30 minutes?*

---

## What deliberately isn't a card

**Classification** ships as audited, correctable metadata — a gate on it would be a rubber stamp ([ADR-54](../../adr/54-two-decision-kinds-batch-worklists.md)). **High-cardinality screening** (a coverage report with dozens of keep/reject calls) becomes a Bases-backed batch worklist plus *one* aggregate work-prompt card — never N cards, which would flood a queue meant to converge to zero and train select-all-accept. And there is no `review-request` type: any card awaiting the PI is simply in `proposed`, pointing at the artifact under review.

---

## Related

- Conceptual overview: [Kanban board](README.md)
- State machine: [Board states and the review gate](states.md)
- The decision-kind model the card serves: [Why promotion is gated](../knowledge/promotion-model.md)
- The card types in the type system: [Note types and epistemic roles](../knowledge/note-types.md)
- How policy gates writes: [Policy MCP](../../reference/policy-mcp.md)
