---
topic: workflows
---

# Assess

**Group.** Downstream (stage workflow)
**Goal.** Map the corpus for a project: identify what's ready, what's thin, what's missing. Produce a corpus map the human can use to decide whether to write now or read more first.

## Pipeline position

First downstream stage; precondition for [Frame](frame.md).

## Steps

1. The human creates a project folder: `40-workbench/<project>/` with a `brief.md` describing the deliverable, audience, length, and framing constraints.
2. A `scope-project` card opens on the project. Mapper claims it.
3. Mapper runs `scope-project` (see [profiles/README.md](../../../reference/profile-matrices.md#lane-permissions-matrix)): retrieves all claim and reference notes matching the brief topic; computes cluster density, recency distribution, source diversity; identifies adjacent topics with thin coverage.
4. The output is written to `40-workbench/<project>/01-map/corpus-map.md` as a structured report.
5. The card completes to `done` (`review_status: requested`). Human reads the corpus map and decides: proceed to [Frame](frame.md), or pause to read more (loops back to [Zotero Capture](../upstream/zotero-capture.md) / [Find](../upstream/find.md)).

## Owners

Mapper executes the `scope-project` retrieval (read-only across the vault, writes only to the corpus-map artifact). Human owns the "is this ready to write?" decision.

## Card lifecycle

`ready` if watcher-created (file-system watcher on new `brief.md`) OR `triage` if human-created via `Memoria: new project` (human transitions to `ready` after reviewing the auto-populated brief fields) → `running` (Mapper claims) → `done` with `review_status: requested` and `corpus-map.md` written → human reads, decides: `approved` (advances to [Frame](frame.md)) or `rejected` (human typically spawns new cards in [Find](../upstream/find.md) to read more first; the original is archived with `metadata.archive_reason: superseded` when the revision card opens, or `metadata.archive_reason: discarded` if the assessment is abandoned).

## Command

`hermes -p memoria-mapper run scope-project --project <project-name>`.

## Why not skip straight to drafting

Humans almost always overestimate corpus readiness — they remember the notes they've recently touched, not the gaps they haven't. The corpus map surfaces the gaps. A ten-minute assessment saves writing a chapter on thin evidence.

## Related

- **Profile:** [profiles/mapper.md](../../../explanation/profiles/mapper.md)
- **Next workflow:** [Frame](frame.md)
- **Umbrella workflow:** [Write](write.md)
