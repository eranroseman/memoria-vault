---
title: Classify a source
parent: Library
grand_parent: How-to guides
nav_order: 4
---

# Classify a source

Settle a paper's `research_area` (and `methodology`) when ingest couldn't decide on its own.

Classifying tags a paper with its field of study. When a source comes in, ingest fills these tags in automatically wherever the answer is clear. Most of the time you do nothing. This guide covers the cases where the work lands on you.

Three situations bring you in:

| Situation | What it means |
| --- | --- |
| Genuine ambiguity | Ingest left the field blank and raised a `flag` card with candidate values and scores. It reports; you decide. |
| Draft to review | The Librarian parked a suggested value in `_proposed_classification`, separate from the real fields. |
| Correction | Ingest applied a value you disagree with; edit the frontmatter directly. |

For what ingest decides and how, see [Ingest routing](../../reference/ingest.md).

## Prerequisites

- A source ingested to `catalog/sources/<source_id>/source.md` ([Capture and ingest a source](capture-and-ingest.md))

## Steps

**1. Handle any `flag` card first.**

Open the Inspector or queue surface for source metadata findings. If ingest hit
genuine ambiguity, you'll see a finding for the source. Pick the right value,
write it into the source Concept frontmatter at
`catalog/sources/<source_id>/source.md`, then resolve the attention item.

**2. Open the source and check what ingest applied.**

In `catalog/sources/<source_id>/source.md`, compare source metadata against the
source itself. If a value is wrong, edit the frontmatter directly; the worker
observes and backfills the PI edit.

Every decision, applied or flagged, is logged as one line in `system/logs/classify.jsonl`. That audit line is what makes a value safe to correct by hand. The thresholds ingest uses (`classify.confidence_floor`, `classify.near_tie_margin`) live in `.memoria/schemas/calibration.yaml`.

**3. Accept the Librarian's draft, if there is one.**

Look for a `_proposed_classification` block in the frontmatter. This is the Librarian's draft, parked in a holding area apart from the real fields. Read each proposed value. Copy the ones you accept — edited for accuracy — into the main frontmatter, then delete the whole `_proposed_classification:` block. The block is temporary and should not be left behind.

The `projects` sub-key inside the draft isn't a guess: it's derived from your optional [project hints](../setup/configure-project-hints.md).

**4. Confirm the source reads `lifecycle: current`.**

A source is created at `lifecycle: current` once checked. Classifying does not
change the source lifecycle. Confirm it still reads `current`, then resolve the
attention item:

```yaml
lifecycle: current
```

**5. Reuse the same terms in notes and hubs.**

When you write checked notes or hubs from this source, use the same vocabulary.
Mismatched vocabulary between the catalog and knowledge graph is what makes
later queries miss results ([Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)).

## Verify

- The source reads `lifecycle: current`, has settled metadata, and no longer has a `_proposed_classification` block
- No `flag` card for this citekey is still at `proposed` in your queue
- `system/logs/classify.jsonl` records the decision (applied or flagged) for this citekey

## Related

- Previous step: [Capture and ingest a source](capture-and-ingest.md)
- Next step: [Discuss a paper](discuss-a-paper.md)
- The automation's thresholds and audit trail: [Ingest routing](../../reference/ingest.md)
- Field semantics: [Frontmatter fields](../../reference/frontmatter.md)
- Optional per-project hints the proposal draws on: [Configure project hints](../setup/configure-project-hints.md)
