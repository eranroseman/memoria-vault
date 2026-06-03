---
title: The Mapper
parent: Profiles
---


# The Mapper

The Mapper is the lens on what the human already has. It produces scope reports, gap reports, and cluster density maps over the existing corpus. Its defining constraint is **read-only across canonical content**: Mapper never proposes new sources, never composes claims, never edits notes. Its value is giving the human a view of their corpus that would take hours to construct by hand.

---

## Why it's designed this way

**Reproducible maps, not opinionated summaries.** Mapper's map of a corpus should be the same today and next week, given the same vault state. HDBSCAN clustering, embedding similarity, and recency aggregation are all deterministic. The LLM composes the prose over deterministic outputs. This reproducibility is what makes Mapper's outputs usable as a *decision basis* — if the map changes on every run, the human can't rely on it to decide whether to write now or read more.

**Read-only across canonical content.** The Mapper never writes to canonical content; its only writes are to its own project scratch (`40-workbench/*/01-map/`, covered next). (The per-source comparative `[!brief]` lives at the top of a paper note in `20-sources/`, which only the Librarian may write — so that callout is composed by the Librarian during ingest, not the Mapper. See [the Librarian](librarian.md).)

**Project-scratch-only writes.** Mapper writes only to `40-workbench/*/01-map/`. This protects against accidental pollution of canonical zones from corpus-mapping operations. A Mapper session that accidentally wrote to `30-synthesis/` would be difficult to audit; restricting it to project scratch keeps the operation clean.

---

## What the Mapper is not

**Not Librarian.** Librarian and Mapper share retrieval tooling but face opposite directions. Librarian reaches outward to discover new sources; Mapper surveys what already exists. Mapper cannot reach external APIs at all — that's not an oversight, it's the separation of inward and outward retrieval into profiles with different postures.

**Not Writer.** Mapper produces maps; Writer produces arguments from maps. A corpus map might say "you have 23 claim notes on JITAI receptivity, with recency tilted 2024–2025." It does not conclude "you have enough to write" — that judgment is the human's. The distinction matters because conflating mapping with arguing blurs who is responsible for the argument's quality.

**Not Verifier.** Both are read-only, but they serve different concerns. Verifier traces claim *provenance* — did this draft cite its sources correctly? Mapper surveys corpus *structure* — what do you have, how is it clustered, where are the gaps? Same constraint, different question.

**Not a chat surface.** Mapper outputs are structured artifacts (`corpus-map.md`, `gap-report.md`, cluster maps) with declared inputs, not conversational answers. For ad-hoc questions about the corpus, Socratic is the right tool.

---

## Related

**Explanation**

- Directional counterpart: [Librarian](librarian.md)
- Content counterpart: [Writer](writer.md)
- Why the map/argument split matters: [why specialist profiles](../rationale/why-specialist-profiles.md)

**How-to**

- Workflow: [assess your corpus](../../how-to-guides/writing/assess-your-corpus.md)
