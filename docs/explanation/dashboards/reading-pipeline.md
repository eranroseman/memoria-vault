---
topic: dashboards
---

# `reading-pipeline` — design summary

**Runtime artifact.** Ships at `00-meta/01-dashboards/reading-pipeline.md` in the [starter vault](https://github.com/eranroseman/memoria-vault) and runs in Obsidian via Dataview; the runtime queries live there. This page covers the design role.

## Mission

Keep papers flowing through the upstream pipeline and show what's stuck. The human opens this when the inbox feels full and they need to decide what to process next. Two views: papers in active processing (`lifecycle: proposed`), and claim notes by maturity (downstream of processing). Together they answer "what should I read next?" and "what came out of my recent reading?"

## What this dashboard is not

- **Not [`discuss-queue`](discuss-queue.md).** Discuss-queue is narrowly scoped to fully-classified (`lifecycle: current`) paper notes that haven't yet had a Socratic pass — the upstream-cognitive-discipline view. Reading-pipeline is the broader working surface: papers still in active processing (`lifecycle: proposed`) plus downstream claim-note maturity. Reading-pipeline asks "what's in flight?"; discuss-queue asks "what owes me a Socratic conversation?"
- **Not [`weekly-review`](weekly-review.md).** Weekly is a ritual entry point; reading-pipeline is a working surface used between rituals.
- **Not a board view.** It queries note state (paper-note `lifecycle` and claim-note `maturity`), not card state. [`board-state`](board-state.md) is the card view.

## Design decisions

- **Two queries, two cadences.** "Papers in active processing" answers a near-term question (what to read this session). "Claim notes by maturity" answers a longer-term question (what's the durable output of all this reading). Surfacing both in one dashboard prevents the human from optimizing one without watching the other.
- **`proposed` lifecycle is the in-flight signal.** A paper note moves from `proposed` to `current` when the human (or Verifier) finishes classification. Reading-pipeline shows everything currently `proposed` — the pipeline's middle band.
- **Sort by `file.mtime` not by created date.** Recency of touch matters more than recency of ingest: a paper classified 6 months ago and edited yesterday is more likely the human's current focus than one ingested yesterday but not yet touched.

## Related

- [`discuss-queue`](discuss-queue.md) — the narrower upstream-discipline view
- [`weekly-review`](weekly-review.md) — links to reading-pipeline as the weekly reading-planning step
- [workflows/upstream/discuss.md](../../how-to/workflows/upstream/discuss.md) — the Discuss stage that drains the queue
- [vault/README.md](../vault/README.md) — definitions of the `lifecycle` and `maturity` states
