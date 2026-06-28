---
title: Promotion and gated zones
parent: Knowledge
grand_parent: Explanation
nav_order: 4
---

# Promotion and gated zones

Promotion is the act of making content canonical — confirming a claim into `notes/claims/`, curating a hub, accepting a proposed link. In Memoria it is always a human act. Agents and operations stage proposals; the PI decides what becomes part of the record.

---

## What "canonical" means now

The gated zones are `notes/claims/` 🔒 and `notes/hubs/` 🔒. Project notes add a gated thesis promotion path, and a composition's `deliverable` state remains later work. Content there is trusted: when the Peer-reviewer (the background agent that checks drafts and citations — see [Glossary](../../reference/glossary.md)) traces a draft's citations, it assumes the claims represent positions the PI actually holds; when the PI builds on a claim, they assume they once made it theirs. If those zones could be written without review, every downstream use of canonical content would become suspect.

Promotion is not a file move ([ADR-50](../../adr/50-universal-lifecycle-and-maturity.md)). A note is born in its type-home and stays there; what the gate controls is the **state transition** (a fleeting thought becoming a `current` claim, a proposed link becoming part of the graph) and the **write into a gated zone**. The policy gate enforces the boundary mechanically: agents write staging and ungated zones; gated-zone writes, promotions, the `retracted` decision, and the archive move are PI-only.

What is deliberately *not* gated: the Catalog. Entity records are clean mechanical extractions of given facts — gating them would be a rubber stamp. Where the ingest operation's confidence drops (entity resolution, dedup, license calls), it raises a `flag` instead of merging silently.

---

## What the gate hands you

The review gate hands the PI a proposal, not a verdict. Proposal cards carry an
honest argument; verification cards lead with the finding. The card shapes are
explained in [The honesty card](../kanban-board/honesty-card.md). The broader
decision taxonomy — approval gates, work prompts, batch worklists, and automated
steps — lives in [Decision points](../kanban-board/decision-points.md).

---

## Maturity is a signal, not a gate

Claims carry `maturity` (`seedling → budding → evergreen`) — a soft, PI-set signal of how developed the claim is. It gates nothing and nothing auto-promotes at `evergreen`. Likewise `agent_recommendation` is a soft, agent-set verdict on a check; a `clean` recommendation never substitutes for human approval. The two axes — "how trusted?" (lifecycle) and "how developed?" (maturity) — are visibly different, with distinct value sets, so neither can impersonate the other.

A common pitfall is deferring promotion until a claim "feels evergreen." That misreads the model: make a claim `current` when you have decided it represents your position; maturity tracks how developed it is afterward.

---

## Related

**Explanation**

- The types and zones involved: [Document types and epistemic roles](document-types.md)
- Why state replaced folders: [Lifecycle, not topic — and state, not folders](../../design/lifecycle-over-topic.md)
- The card fields in detail: [The honesty card](../kanban-board/honesty-card.md)
- Approval gates vs work prompts: [Decision points](../kanban-board/decision-points.md)
- The board mechanics behind the review gate: [Board states and the review gate](../kanban-board/states.md)
- Why promotion is gated: [Why the review gate is structural](../../design/why-review-gate-is-structural.md)

**Decisions**

- [ADR-51](../../adr/51-inbox-category-and-honesty-card.md) — the Inbox category and the honesty card
- [ADR-54](../../adr/54-two-decision-kinds-batch-worklists.md) — approval gates vs work prompts; classify automated; batch worklists
