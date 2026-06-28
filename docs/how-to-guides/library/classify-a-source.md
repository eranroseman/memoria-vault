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

- A paper ingested to `catalog/papers/<citekey>.md` ([Capture and ingest a source](capture-and-ingest.md))

## Steps

**1. Handle any `flag` card first.**

Open your queue from the navigator rail on the left: **Now** → **Action queue** opens the **Inbox** queue; its **Needs me** view lists what's waiting. If ingest hit genuine ambiguity, you'll see a card titled something like "Ambiguous research area for `<citekey>`". It reports the `finding` and the scored candidates, but states no verdict — you choose. Pick the right value, write it into the paper's frontmatter at `catalog/papers/<citekey>.md`, then resolve the card ([Work the review queue](../inbox/work-the-review-queue.md)).

**2. Open the paper and check what ingest applied.**

In `catalog/papers/<citekey>.md`, compare `research_area` and `methodology` against the paper itself. If a value is wrong, **edit the frontmatter directly** — there is nothing to approve.

Every decision, applied or flagged, is logged as one line in `system/logs/classify.jsonl`. That audit line is what makes a value safe to correct by hand. The thresholds ingest uses (`classify.confidence_floor`, `classify.near_tie_margin`) live in `.memoria/schemas/calibration.yaml`.

**3. Accept the Librarian's draft, if there is one.**

Look for a `_proposed_classification` block in the frontmatter. This is the Librarian's draft, parked in a holding area apart from the real fields. Read each proposed value. Copy the ones you accept — edited for accuracy — into the main frontmatter, then delete the whole `_proposed_classification:` block. The block is temporary and should not be left behind.

The `projects` sub-key inside the draft isn't a guess: it's derived from your optional [project hints](../setup/configure-project-hints.md).

**4. Confirm the paper reads `lifecycle: current`.**

A paper is created at `lifecycle: current` straight away — Catalog facts don't wait in a queue. (What sits at `proposed` is the candidate *card* in your queue, not the paper.) Classifying doesn't change the paper's lifecycle. Confirm it still reads `current`, then resolve the candidate card:

```yaml
lifecycle: current
```

**5. Reuse the same terms in your source note.**

When you fill the source note in `notes/sources/`, use the same `research_area` / `methodology` values you settled here. Mismatched vocabulary between the catalog and your notes is what makes later queries miss results ([Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)).

## Verify

- The paper reads `lifecycle: current`, has a settled `research_area`, and no longer has a `_proposed_classification` block
- No `flag` card for this citekey is still at `proposed` in your queue
- `system/logs/classify.jsonl` records the decision (applied or flagged) for this citekey

## Related

- Previous step: [Capture and ingest a source](capture-and-ingest.md)
- Next step: [Discuss a paper](discuss-a-paper.md)
- The automation's thresholds and audit trail: [Ingest routing](../../reference/ingest.md)
- Field semantics: [Frontmatter fields](../../reference/frontmatter.md)
- Optional per-project hints the proposal draws on: [Configure project hints](../setup/configure-project-hints.md)
