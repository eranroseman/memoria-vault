---
title: Why promotion is gated
parent: Knowledge
nav_order: 5
---

# Why promotion is gated

Promotion is the act of making content canonical — confirming a claim into `notes/claims/`, curating a hub, accepting a proposed link. In Memoria it is always a human act. The rule for every actor that is not the PI is **propose, not dispose**: agents and engines stage proposals; the PI decides what becomes part of the record. This is not a safeguard bolted onto the system — it is the mechanism that keeps the vault trustworthy.

---

## What "canonical" means now

The gated zones are `notes/claims/` 🔒 and `notes/hubs/` 🔒. Project notes add a gated thesis promotion path, and a composition's `deliverable` state remains later work. Content there is trusted: when the Peer-reviewer traces a draft's citations, it assumes the claims represent positions the PI actually holds; when the PI builds on a claim, they assume they once made it theirs. If those zones could be written without review, every downstream use of canonical content would become suspect.

Since lifecycle moved out of the folders ([ADR-50](../../adr/50-universal-lifecycle-and-maturity.md)), promotion is no longer a file move. A note is born in its type-home and stays there; what the gate controls is the **state transition** (a fleeting thought becoming a `current` claim, a proposed link becoming part of the graph) and the **write into a gated zone**. The policy gate enforces the boundary mechanically: agents write staging and ungated zones; gated-zone writes, promotions, the `retracted` decision, and the archive move are PI-only.

What is deliberately *not* gated: the Catalog. Entity records are clean mechanical extractions of given facts — gating them would be a rubber stamp. Where the ingest engine's confidence drops (entity resolution, dedup, license calls), it raises a `flag` instead of merging silently.

---

## The honesty card: what an approval gate hands you

The gate hands the PI a proposal, not a verdict. A proposal card carries an honest argument (with the agent's strongest self-rebuttal) and no verdict line; a verification card leads with the finding instead. Why that shape defeats automation bias — and the per-card field breakdown — is developed in [The honesty card](../kanban-board/card-schema.md) (fields in [Frontmatter fields](../../reference/frontmatter.md#the-honesty-card-fields)). The rule it serves: *an Inbox item a human can clear without reading is a design smell.*

---

## Two kinds of decision point

Not every place the PI acts is an approval ([ADR-54](../../adr/54-two-decision-kinds-batch-worklists.md)):

- **Approval gates** review agent-produced output: candidate triage (keep this source?), link confirmation (with evidence and stance reasoning per edge), certification before shipping, re-adjudication after a retraction, near-tie dedup calls, the archive proposal. Each ships its reasoning as an honesty card.
- **Work prompts** signal that it is time for the PI's *own* thinking: "this kept source is worth distilling into claims," "this corpus is ready to write from." They are rich nudges with the material to start — not approvals, and never blocking.

**Classify is neither — it is automated.** Assigning facet metadata to a kept source is low-stakes, high-volume, and verifiable: a human gate on it is a guaranteed rubber stamp. So classification ships as audited, correctable metadata, with a `flag` only on genuine ambiguity. Prefer full automation over a fake decision.

**High-cardinality decisions become a batch worklist, never N cards.** When a coverage report finds forty sources each needing a keep/reject call, the Inbox gets *one* aggregate work-prompt ("40 sources to screen"), pointing at a Bases-backed worklist where each file-backed row carries a `decision` field the PI toggles at group or item granularity — the systematic-review screening model. Forty cards would flood a queue meant to converge to zero and train select-all-accept.

And nowhere is there confidence-tiered auto-accept: confident-wrong is exactly the failure the gate exists to catch.

---

## Maturity is a signal, not a gate

Claims carry `maturity` (`seedling → budding → evergreen`) — a soft, PI-set signal of how developed the claim is. It gates nothing and nothing auto-promotes at `evergreen`. Likewise `agent_recommendation` is a soft, agent-set verdict on a check; a `clean` recommendation never substitutes for human approval. The two axes — "how trusted?" (lifecycle) and "how developed?" (maturity) — are visibly different, with distinct value sets, so neither can impersonate the other.

A common pitfall is deferring promotion until a claim "feels evergreen." That misreads the model: make a claim `current` when you have decided it represents your position; maturity tracks how developed it is afterward.

---

## Why this feels slow

The human gate is the system's bottleneck by design. Agents can catalog, extract, and draft faster than the PI can review; the proposal queue grows unless the PI keeps pace. A system that could populate `notes/claims/` without the PI's attention would be a system where the PI no longer owns their own knowledge base.

The right response to a full queue is not to automate review but to let the WIP limits and back-pressure bite — the board mechanism that makes the bottleneck visible instead of letting "reviewed" silently degrade into "rubber-stamped." That mechanism, and the rule that a rejected proposal spawns a fresh card rather than reopening the old one, are explained in [Board states and the review gate](../kanban-board/states.md). The gate is also instrumented — time-on-gate and accept-rate feed the fleet-health dashboard — so a gate that has stopped being a real decision shows up in the data.

---

## Related

**Explanation**

- The types and zones involved: [Note types and epistemic roles](note-types.md)
- Why state replaced folders: [Lifecycle, not topic — and state, not folders](lifecycle-over-topic.md)
- The card fields in detail: [The honesty card](../kanban-board/card-schema.md)
- The board mechanics behind the gate: [Board states and the review gate](../kanban-board/states.md)

**Decisions**

- [ADR-51](../../adr/51-inbox-category-and-honesty-card.md) — the Inbox category and the honesty card
- [ADR-54](../../adr/54-two-decision-kinds-batch-worklists.md) — approval gates vs work prompts; classify automated; batch worklists
