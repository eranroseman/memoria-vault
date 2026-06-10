---
title: contradictions dashboard
parent: Synthesis agenda
nav_order: 4
grand_parent: Dashboards
---

# `contradictions` dashboard

Surfaces claim notes that disagree with each other as a synthesis starting point. Open it when building an argument or during the weekly synthesis pass — a cluster of contradictions is usually where the interesting writing is.

## What it shows

Every claim carrying a PI-confirmed `contradicts` link (a typed entry in the note's `links:` block — [ADR-52](../../../adr/52-links-vs-relationships.md)) appears here, listed as conflicting pairs. The pairs are deduplicated — if both claim A and claim B link to each other as contradictions, the pair appears once, not twice. Sorted by most-recently-modified first.

## What it is not

**Not an LLM tension-finder.** The dashboard reads only confirmed `contradicts` links. Links are *authored*: the Librarian's link lane may propose a tension (with evidence and stance reasoning per edge), but the link exists only once the PI confirms it — no model ever auto-writes one.

**Not a truth judgment.** A `contradicts` link says two claims disagree, not which one is right. Resolving the tension is the human's call: soften one, supersede one with a newer claim, or keep both as a live productive debate.

**Not a defect list.** A paper that refutes an earlier one is a wanted finding. The dashboard frames pairs as "worth resolving," never as errors to clear.

## How contradictions differ from supersession

A `contradicts` link records that two *current* claims disagree. `superseded_by` records that one claim *replaced* another over time — the older claim is `retracted`, with the lineage link preserved. A contradiction is an open tension; a supersession is a resolved one.

## Sparseness at the start is expected

Until you confirm `contradicts` links, the dashboard is near-empty. That emptiness is meaningful: it tells you either that your corpus has no disagreements yet (unlikely) or that you haven't been filing contradiction links while reading. The first time you find yourself writing "paper X contradicts what I noted from paper Y," file the link and open this dashboard.

## Related

- [open-questions dashboard](open-questions.md) — closest sibling; both build the synthesis agenda
- Setting the contradicts links: [Link related claims](../../../how-to-guides/compile/link-related-claims.md)
- Sweeps that surface contradictions: [Run a retraction sweep](../../../how-to-guides/operate/run-a-retraction-sweep.md)
- [Wikilink and link conventions](../../../reference/linking.md) — the `links:` block and the typed-link vocabulary
