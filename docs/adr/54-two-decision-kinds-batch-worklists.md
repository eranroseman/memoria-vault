---
topic: decisions
id: 54
title: Two kinds of human decision — approval gates and work prompts; classify automated; batch worklists for high cardinality
status: accepted
date_proposed: 2026-06-10
date_resolved: 2026-06-10
assumes: [3, 51]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 54
---

# ADR-54: Two kinds of human decision — approval gates and work prompts; classify automated; batch worklists for high cardinality

## Context

Reviewing every human touchpoint with one question — *could the PI clear this without
reading it?* — exposed that the gates were not one kind of thing: some review agent
output, some prompt the PI's own thinking, and one (classify) was a rubber-stamp
pretending to be a gate (D21/D37; reinforces [ADR-03](03-structural-review-gate.md)
and the no-auto-accept rule).

## Decision

Every place the PI acts is one of **two kinds**, and each gets a different Inbox item:

- **Approval gate** — the PI reviews *agent-produced output* and accepts/rejects. The
  item must carry the honesty card ([ADR-51](51-inbox-category-and-honesty-card.md)) —
  never a bare "OK?".
- **Work prompt** — the agent signals it is *time for the PI's own thinking/writing*;
  a rich nudge with the material to start, not an approval.

**The rule:** *an Inbox item a human can clear without reading is a design smell* —
give it real decision material, or automate it. **classify fails this test and is
automated** (audited, correctable; a `flag` fires only on genuine ambiguity) — the real
Read-side gates are candidate triage (keep/skip) and link confirmation.
**High-cardinality per-item decisions live in a batch worklist** — a Bases-backed
screening surface where each file-backed `worklist-item` row carries a `decision`
field the PI toggles at group or item granularity — surfaced as **one aggregate
work-prompt**, never N cards.
No confidence-tiered auto-accept anywhere: confident-wrong is the failure mode the
gate exists to catch.

## Consequences

- Each decision point in the workflow is classified (gate vs prompt) and its Inbox
  item designed accordingly; new features must declare which kind they add.
- Classification ships as audited metadata the PI can correct, not as a card.
- Batch screening borrows the systematic-review model (include/exclude with reasons),
  and its worklists converge — the Inbox stays an action queue that empties.
- The strongest gates (certify, link-confirm, re-adjudicate) always ship their
  reasoning.

## Alternatives considered

**A gate on classify.** Low-stakes metadata + high volume = guaranteed rubber-stamp;
automation with audit beats a fake decision. **One card per screened item.** Floods
the queue and trains select-all-accept. **Confidence-tiered auto-accept.** Waves
through exactly the confident-wrong outputs the gate exists to catch.

## Related

- **Related decisions / Depends on:** [ADR-03](03-structural-review-gate.md),
  [ADR-51](51-inbox-category-and-honesty-card.md), [ADR-15](15-project-membership-from-topic-hint.md)
