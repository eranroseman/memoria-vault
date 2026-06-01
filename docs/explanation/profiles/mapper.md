
# The Mapper

The Mapper is the lens on what the human already has. It produces scope reports, gap reports, cluster density maps, and comparative briefs over the existing corpus. Its defining constraint is **read-only across canonical content**: Mapper never proposes new sources, never composes claims, never edits notes. Its value is giving the human a view of their corpus that would take hours to construct by hand.

---

## Why it's designed this way

**Reproducible maps, not opinionated summaries.** Mapper's map of a corpus should be the same today and next week, given the same vault state. HDBSCAN clustering, embedding similarity, and recency aggregation are all deterministic. The LLM composes the prose over deterministic outputs. This reproducibility is what makes Mapper's outputs usable as a *decision basis* — if the map changes on every run, the human can't rely on it to decide whether to write now or read more.

**The comparative-brief is Mapper's quiet presence.** The `[!brief]` callout at the top of every new paper note is produced by Mapper during ingest. It's the system's answer to "how does this new source relate to what I already have?" without requiring the human to survey the whole corpus first. This is a significant UX benefit delivered with minimal friction: one read-only operation, one callout, delivered automatically.

**Project-scratch-only writes.** Mapper writes only to `40-workbench/*/01-map/`. This protects against accidental pollution of canonical zones from corpus-mapping operations. A Mapper session that accidentally wrote to `30-synthesis/` would be difficult to audit; restricting it to project scratch keeps the operation clean.

---

## What the Mapper is not

**Not Librarian.** Librarian and Mapper share retrieval tooling but face opposite directions. Librarian reaches outward to discover new sources; Mapper surveys what already exists. Mapper cannot reach external APIs at all — that's not an oversight, it's the separation of inward and outward retrieval into profiles with different postures.

**Not Writer.** Mapper produces maps; Writer produces arguments from maps. A corpus map might say "you have 23 claim notes on JITAI receptivity, with recency tilted 2024–2025." It does not conclude "you have enough to write" — that judgment is the human's. The distinction matters because conflating mapping with arguing blurs who is responsible for the argument's quality.

**Not Verifier.** Both are read-only, but they serve different concerns. Verifier traces claim *provenance* — did this draft cite its sources correctly? Mapper surveys corpus *structure* — what do you have, how is it clustered, where are the gaps? Same constraint, different question.

**Not a chat surface.** Mapper outputs are structured artifacts (`corpus-map.md`, `gap-report.md`, comparative-brief callouts) with declared inputs, not conversational answers. For ad-hoc questions about the corpus, Socratic is the right tool.

---

## Related

- Directional counterpart: [Librarian](librarian.md)
- Content counterpart: [Writer](writer.md)
- Workflow: [assess your corpus](../../how-to-guides/writing/assess-your-corpus.md)
- Why the map/argument split matters: [why specialist profiles](../architecture/why-specialist-profiles.md)
