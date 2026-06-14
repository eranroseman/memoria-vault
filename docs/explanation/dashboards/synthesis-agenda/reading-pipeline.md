---
title: The reading-pipeline dashboard
parent: Synthesis agenda
nav_order: 1
grand_parent: Dashboards
---

# The reading-pipeline dashboard

Open the reading-pipeline dashboard during a reading session when the queue feels full and you need to decide what to process next.

---

## What it shows

It shows what is in flight on the Library side and what has come out the other side — answering two questions at once: "what should I read next?" (source notes in `notes/source/` at `lifecycle: proposed`, awaiting reading) and "what came out of my recent reading?" (claims in `notes/claims/` grouped by `maturity`). Sources you've read but not yet distilled into claims sit at `lifecycle: provisional` in between. The two halves together make visible whether reading is converting into synthesis.

---

## What this dashboard is not

**Not [The discuss-queue dashboard](discuss-queue.md).** The discuss-queue is narrowly scoped to read-but-not-distilled sources that would benefit from a Co-PI pass — one specific Library-side debt. Reading-pipeline is the broader working surface: sources in active processing plus the resulting claim maturity. Reading-pipeline asks "what's in flight?"; discuss-queue asks "what owes me a conversation?"

**Not [The weekly-review dashboard](../structural-health/weekly-review.md).** Weekly-review is a scheduled ritual with a fixed top-to-bottom order. Reading-pipeline is a working surface consulted between rituals, when deciding what to pick up next in a given session.

**Not a board view.** This dashboard queries note state — source-note `lifecycle` and claim `maturity` — not cards. The [The board-state dashboard](../daily-glance/board-state.md) view is the card side.

---

## Why it's designed this way

**Two Bases views, two cadences.** "Sources awaiting reading" answers a near-term question: what should I read this session? "Claims by maturity" answers a longer-term question: what is the durable output of all this reading? Showing both in one dashboard prevents optimizing one measure while ignoring the other — reading without synthesis, or synthesis without new sources.

**Source `lifecycle` is the in-flight signal.** A source note is `proposed` from the moment it's created until the PI reads it, then `provisional` once read but not yet distilled into claims, reaching `current` only when its claims are written. Reading-pipeline shows the `proposed` and `provisional` sources in `notes/source/` — the pipeline's working middle band. (The Catalog entity behind each source is already `current` — facts don't queue; the *reading* does.)

**Sort by modification time, not creation date.** Recency of touch matters more than recency of intake. A source kept six months ago and annotated yesterday is more likely the PI's current focus than one catalogued yesterday but not yet touched.

---

## Related

- Narrower Library-discipline sibling: [The discuss-queue dashboard](discuss-queue.md)
- Weekly entry point that links to this: [The weekly-review dashboard](../structural-health/weekly-review.md)
- The state model behind `proposed`/`provisional`: [Lifecycle, not topic — and state, not folders](../../knowledge/lifecycle-over-topic.md)
- Next step after the pipeline surfaces a source: [Discuss a paper](../../../how-to-guides/compile/discuss-a-paper.md)
