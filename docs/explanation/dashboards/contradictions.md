# `contradictions` dashboard

Surfaces claim notes that disagree with each other as a synthesis starting point. Open it when building an argument or during the weekly synthesis pass — a cluster of contradictions is usually where the interesting writing is.

## What it shows

Every `claim-note` carrying a human-set `relations.contradicts` link appears here, listed as conflicting pairs. The pairs are deduplicated — if both claim A and claim B link to each other as contradictions, the pair appears once, not twice. Sorted by most-recently-modified first.

## What it is not

**Not an LLM tension-finder.** The dashboard reads only human-set `relations.contradicts` links. No model judges which claims conflict. The NLI-based proposer that would suggest contradiction pairs for human confirmation is deferred future work — it would never auto-write a link.

**Not a truth judgment.** A `contradicts` link says two claims disagree, not which one is right. Resolving the tension is the human's call: soften one, supersede one with a newer claim, or keep both as a live productive debate.

**Not a defect list.** A paper that refutes an earlier one is a wanted finding. The dashboard frames pairs as "worth resolving," never as errors to clear.

## How contradictions differ from supersession

`relations.contradicts` records that two *current* claims disagree. `superseded_by` records that one claim *replaced* another over time — the older claim is retired. A contradiction is an open tension; a supersession is a resolved one.

## Sparseness at the start is expected

Until you file `contradicts` links, the dashboard is near-empty. That emptiness is meaningful: it tells you either that your corpus has no disagreements yet (unlikely) or that you haven't been filing contradiction links while reading. The first time you find yourself writing "paper X contradicts what I noted from paper Y," file the link and open this dashboard.

## Related

- [explanation/dashboards/open-questions.md](open-questions.md) — closest sibling; both build the synthesis agenda
- Setting the contradicts relations: [link-related-claims.md](../../how-to-guides/sources/link-related-claims.md)
- Sweeps that surface contradictions: [run-a-retraction-sweep.md](../../how-to-guides/maintenance/run-a-retraction-sweep.md)
- [reference/linking.md](../../reference/linking.md) — the `relations:` block and typed-relation vocabulary
