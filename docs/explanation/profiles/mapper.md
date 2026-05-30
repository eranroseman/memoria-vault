---
topic: profiles
---

# Mapper — design summary

**Runtime contract.** Full prompt and operational details live at `.memoria/profiles/memoria-mapper/SOUL.md` in the starter vault.

## Mission

Mapper is the lens on what the human already has. It produces scope reports, gap reports, cluster density maps, and comparative briefs over the existing corpus. The defining trait is **read-only across canonical content**: Mapper never proposes new sources, never composes new claims, never edits paper notes. Its value is in giving the human a view of the corpus that would take hours to assemble by hand.

## What this profile is not

- **Not Librarian.** Same retrieval tooling, opposite direction (see [Profile boundaries](README.md#profile-boundaries)); and unlike Librarian, Mapper cannot reach external APIs at all (`external_api_policy: blocked`).
- **Not Writer.** Mapper produces maps; Writer produces arguments. A corpus-map says "you have 23 claim notes on JITAI receptivity, recency tilted 2024–2025." It does not say "you have enough to write" — that judgment is the human's.
- **Not Verifier.** Both are read-only, but they serve different concerns. Verifier traces claims to sources (provenance check). Mapper surveys clusters and gaps (corpus structure).
- **Not a chat surface for free-form questions.** Mapper outputs are structured artifacts (`corpus-map.md`, `gap-report.md`, `[!brief]` callouts) with cited inputs, not conversational responses. For ad-hoc questions about the corpus, the human switches to Socratic.

## Design decisions

- **Read-only by policy, even for scratch.** Mapper writes only under `40-workbench/*/01-map/` — `corpus-map.md`, `gap-report.md`, `comparative-briefs/`, and `cluster-maps/`. Project scratch only — nowhere else. This protects against accidental canonical pollution from corpus-mapping operations (e.g., a stray write to `30-synthesis/` while computing a cluster).
- **Deterministic ML layer with LLM narrative composition.** Mapper's value is the *reproducibility* of the maps — HDBSCAN cluster identification, embedding similarity, recency aggregation are all deterministic. The LLM only composes prose over those deterministic outputs. The pattern is documented as the definitive hybrid in [architecture/why-computational-methods.md](../architecture/why-computational-methods.md).
- **Output is a map, not an argument.** Every Mapper artifact declares its inputs in frontmatter (`sources:` — which folders, what date range, which `qmd` index version). The human can rerun and get an identical map; they can audit which slice of the corpus was scanned.
- **Comparative-brief drives the `[!brief]` inline callout.** Mapper's only direct presence outside dashboards and project scratch is the comparative-read callout that appears at the top of new paper notes. It's the design's answer to "how does a new source relate to what I already have?" without requiring the human to read the whole corpus first.

## Permissions and commands

Folder permission matrix lives in [profiles/README.md](../../reference/profile-matrices.md#folder-permission-matrix); the runtime contract (full command list, deterministic/hybrid annotations per command, exit conditions) lives in the SOUL.md.

## Related

- Workflows: [assess](../../how-to/workflows/downstream/assess.md), [refactor](../../how-to/workflows/maintenance/refactor.md), [ingest §`comparative-brief`](../../how-to/workflows/upstream/ingest.md)
- Pilot: [E1 Open Notebook](../../project/roadmap/pilots/01-open-notebook.md) — active experiment using Open Notebook as the LLM back-end for narrative composition in `comparative-brief`.
- Method class: [architecture/why-computational-methods.md](../architecture/why-computational-methods.md) — Mapper is the definitive hybrid profile.
- Reference: [architecture/computational-toolbox.md](../../reference/architecture/computational-toolbox.md) — the embedding, clustering, and search primitives Mapper relies on.
