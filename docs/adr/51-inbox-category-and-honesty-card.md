---
topic: decisions
id: 51
title: The Inbox category and the honesty card — argument for/against, what tipped it, certainty; no verdict on proposals
status: accepted
date_proposed: 2026-06-10
date_resolved: 2026-06-10
assumes: [47, 50]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 51
---

# ADR-51: The Inbox category and the honesty card — argument for/against, what tipped it, certainty; no verdict on proposals

## Context

Agent→human signals were scattered (candidate notes in a folder, board cards, dashboard
rows), and the card format begged the automation-bias question: research shows handing
a human a confident verdict *reduces* scrutiny, and for a proposal the verdict is a
**given** — the agent surfaced the item because it recommends it. The design update
(D6/D18/D35/D37/D49) made the signal end of the loop first-class and made honesty the
card's guardrail.

## Decision

**`inbox/` is the agent→human message category.** Four message card types — **candidate** (a
*found* source proposed for intake), **gap** (a *missing*-source need), **flag** (a
verification/integrity issue), **alert** (drift/retraction) — plus the aggregate
**work-prompt** (below), for **five** Inbox card types in all — on the universal
lifecycle chain (`proposed` = awaiting you; there is no `review-request` type). The
kanban board and the queue dashboards are *views* of the Inbox (one Base grouped by
type).

**Proposal cards carry an honest argument, not a verdict**: **Action** (what you'd be
accepting) · **Argument for** · **Argument against** (the agent's strongest
self-rebuttal) · **What tipped it** (the deciding reason) · **Certainty** (3-level,
action-labelled). No verdict line — it is implied by the card existing.
**Verification/adjudication items keep their verdict** (`clean` / `issues-found` /
`inconclusive`; near-tie same/different/unsure) and lead with the finding.

**High-cardinality decisions never become N cards** — a report that needs dozens of
keep/reject calls is a Bases-backed **batch worklist** and surfaces **one aggregate
work-prompt** in the Inbox.

## Consequences

- "An Inbox item the PI can clear without reading is a design smell" gets structural
  backing: the against-case and certainty are the information-bearing fields.
- Card templates render the honesty body; the schema for each card type lives in
  `.memoria/schemas/types/` like any other type.
- Engines and lanes share one card-writer so every `flag`/`alert`/`candidate` is
  shaped identically.
- Amends [ADR-17](17-shared-candidate-frontmatter.md): `candidate` becomes an Inbox
  type; the shared-frontmatter intent survives inside the card schema.

## Alternatives considered

**Ship the verdict on every card.** Vacuous for proposals and induces automation bias.
**Blind-first (hide the verdict until the PI leans).** There is no verdict to hide on
a proposal; for verification items the finding *is* the payload. **One card per item in
batch screening.** Floods a queue meant to converge to zero and invites
select-all-accept.

## Related

- **Related decisions / Depends on:** [ADR-50](50-universal-lifecycle-and-maturity.md),
  [ADR-03](03-structural-review-gate.md); amends [ADR-17](17-shared-candidate-frontmatter.md)
