# The knowledge cycle

The long-term progression from ingested source to written output. Every note in the vault is somewhere in this cycle; the dashboards surface where things are stuck.

## The seven stages

```text
1. Ingest          → paper-note created, _proposed_classification proposed
2. Classify        → classification promoted, lifecycle: current
3. Synthesize      → claim notes distilled (maturity: seedling)
4. Develop         → cross-referenced, linked into MOCs (maturity: evergreen)
5. Promote         → claim promoted to reference-note when stable enough
6. Write           → reference notes and claims assembled into a draft
7. Export          → draft → deliverable
```

This cycle runs in parallel across many sources. At any given time you will have paper-notes at stage 2, claim notes at stage 3, a growing MOC at stage 4, and an active draft at stage 6. The dashboards show what is stuck at each stage.

## Why stages, not a linear path

The cycle is not strictly sequential. A claim note can be at maturity: seedling for months before a new paper moves it to evergreen. A paper note can sit at "classified" for a year before you have time to distill claim notes from it. The cycle describes the intended direction of flow, not a timeline.

What the cycle prevents: notes that are captured but never synthesized (the most common failure mode), and claims that are synthesized but never written from (the second most common failure mode).

## Where things get stuck

| Stage | Common sticking point | Dashboard that surfaces it |
| --- | --- | --- |
| Ingest → Classify | `_proposed_classification` not reviewed | `reading-pipeline.md` |
| Classify → Synthesize | Reading without writing claim notes | `reading-pipeline.md` (notes in `current` with no linked claims) |
| Synthesize → Develop | Orphan claim notes with no connections | `open-questions.md`, `loose-ends.md` |
| Develop → Write | Claims never assembled into a draft | No dashboard surfaces this directly — it's a judgment call |
| Write → Export | Draft verification finding gaps | `board-state.md` (Verifier cards in review) |

## The compound principle

The cycle is what makes a knowledge system compound rather than just accumulate. A vault that ingests and classifies but never synthesizes is a sophisticated reading list. A vault where claim notes link to each other and to MOCs is a structure you can write from directly — not by remembering what you read, but by navigating a graph of connected ideas.

The measure of a healthy vault is not the number of paper-notes. It is the density of the claim-note layer and the completeness of the MOC layer. A vault with 50 paper-notes and 40 claim notes that link to each other is more useful for writing than a vault with 500 paper-notes and 10 claim notes.

## The weekly ritual's role

The [weekly review](../dashboards/weekly-review.md) ritual is the mechanism that keeps the cycle moving. Without it, ingest accumulates at stage 2 and synthesis never advances. The ritual's seven steps map directly onto the stuck-points table above: triage debt, inbox review, structural checks, and commit.

## Archive at any stage

A note that is no longer useful at any stage should be archived rather than deleted. Set `lifecycle: archived` (or for claim notes, `maturity: retired` and `superseded_by: [[newer-claim]]`), move it to `95-archive/`, and update any backlinks. Archived notes remain readable and in Git history; they disappear from all active Dataview queries and from the agent's search scope.

Archive triggers at each stage:
- **Paper-note:** `pub_status: retracted` or paper no longer relevant to the research direction
- **Claim note:** a newer claim supersedes this one; set `superseded_by:` and `maturity: retired`
- **MOC:** project has ended; MOC documents the intellectual structure of finished work
- **Draft:** submitted or abandoned; move to `50-deliverables/` or `95-archive/`
