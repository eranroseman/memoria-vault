---
title: Classify a source
parent: Library
nav_order: 4
---

# Classify a source

Settle the `research_area` (and `methodology`) the ingest operation couldn't decide on its own ([Ingest routing](../../reference/ingest.md)). Three things land on you — the rest is applied automatically:

- **Genuine ambiguity** — the operation left the field unset and raised one Inbox `flag` card with the top candidates and scores
- **The Librarian's proposal** — the `_proposed_classification` block on the paper entity, promoted by you
- **Corrections** — the automation applied something you disagree with; you edit the frontmatter, no card involved

## Prerequisites

- A paper ingested to `catalog/papers/<citekey>.md` ([Capture and ingest a source](capture-and-ingest.md))

## Steps

**1. Handle any classify `flag` card first.**

If ingest hit genuine ambiguity, a flag card titled along the lines of "Ambiguous research area for `<citekey>`" sits in your Inbox. It carries the `finding` and the scored candidates — never a verdict. Pick the right value, write it into the paper entity's frontmatter yourself, then resolve the card ([Work the review queue](../inbox/work-the-review-queue.md)).

**2. Open the paper entity and review what the automation applied.**

In `catalog/papers/<citekey>.md`, check `research_area` and `methodology` against the paper itself. The thresholds (`classify.confidence_floor`, `classify.near_tie_margin`) live in `.memoria/schemas/calibration.yaml`; every applied or flagged decision is one JSONL line in `system/logs/classify.jsonl`. If a value is wrong, **edit the frontmatter directly** — the audit line is what makes the automation correctable; there is nothing to approve.

**3. Promote the `_proposed_classification` block.**

The Librarian's proposal (LLM hole #1; the `projects` sub-key comes deterministically from your optional [project hints](../setup/configure-project-hints.md)) is a sandboxed namespace in the entity's frontmatter, separate from the main fields. Review each proposed value, copy the ones you accept (edited for accuracy) into the main frontmatter, then delete the entire `_proposed_classification:` block — it is transient.

**4. Confirm the entity's lifecycle.**

A paper entity is created at `lifecycle: current` — Catalog facts don't queue (the thing that sits at `proposed` is the candidate *card* in your Inbox, not the entity). Settling the classification doesn't move the entity's lifecycle; confirm it reads `current` and resolve the candidate card:

```yaml
lifecycle: current
```

**5. Carry the vocabulary into your source note.**

When you fill the source note in `notes/sources/`, reuse the same `research_area` / `methodology` terms — vocabulary drift between catalog and notes is what makes queries lie ([Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)).

## Verify

- The paper entity carries `lifecycle: current`, a settled `research_area`, and no `_proposed_classification` block
- No classify `flag` card for this citekey remains `proposed` in the Inbox
- `system/logs/classify.jsonl` records the decision (applied or flagged) for this citekey

## Related

- Previous step: [Capture and ingest a source](capture-and-ingest.md)
- Next step: [Discuss a paper](discuss-a-paper.md)
- The automation's thresholds and audit trail: [Ingest routing](../../reference/ingest.md)
- Field semantics: [Frontmatter fields](../../reference/frontmatter.md)
- Optional per-project hints the proposal draws on: [Configure project hints](../setup/configure-project-hints.md)
