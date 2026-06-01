
# The reading-pipeline dashboard

Open the reading-pipeline dashboard during a reading session when the inbox feels full and you need to decide what to process next.

---

## What it shows

It shows what is actively in flight through the upstream pipeline and what has come out the other side — answering two questions at once: "what should I read next?" (papers in active processing, by lifecycle stage) and "what came out of my recent reading?" (claim notes grouped by maturity). The two halves together make visible whether reading is converting into synthesis.

---

## What this dashboard is not

**Not [discuss-queue](discuss-queue.md).** The discuss-queue is narrowly scoped to fully-classified paper notes that haven't had a Socratic pass — one specific upstream debt. Reading-pipeline is the broader working surface: papers still in active processing plus downstream claim-note maturity. Reading-pipeline asks "what's in flight?"; discuss-queue asks "what owes me a conversation?"

**Not [weekly-review](weekly-review.md).** Weekly-review is a scheduled ritual with a fixed top-to-bottom order. Reading-pipeline is a working surface consulted between rituals, when deciding what to pick up next in a given session.

**Not a board view.** This dashboard queries note state — paper-note `lifecycle` and claim-note `maturity` — not card state. The [board-state](board-state.md) dashboard is the card view.

---

## Why it's designed this way

**Two queries, two cadences.** "Papers in active processing" answers a near-term question: what should I read this session? "Claim notes by maturity" answers a longer-term question: what is the durable output of all this reading? Showing both in one dashboard prevents optimizing one measure while ignoring the other — reading without synthesis, or synthesis without new sources.

**`lifecycle: proposed` is the in-flight signal.** A paper note lives at `lifecycle: proposed` from the moment it's ingested until the human finishes classification and sets it to `current`. Reading-pipeline shows everything currently `proposed` — the pipeline's working middle band.

**Sort by modification time, not creation date.** Recency of touch matters more than recency of ingest. A paper classified six months ago and edited yesterday is more likely the human's current focus than one ingested yesterday but not yet touched.

---

## Related

- Narrower upstream-discipline sibling: [discuss-queue](discuss-queue.md)
- Weekly entry point that links to this: [weekly-review](weekly-review.md)
- Lifecycle stages explained: [knowledge/lifecycle-over-topic](../knowledge/lifecycle-over-topic.md)
- Next step after the reading-pipeline surfaces a paper: [discuss a paper](../../how-to-guides/sources/discuss-a-paper.md)
