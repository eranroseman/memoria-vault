---
title: Classify a source
parent: Compile
nav_order: 4
---

# Classify a source

In v0.1.0-alpha.2 most classification is **automated**: the ingest engine's classify stage reads the OpenAlex topics already in the enrichment payload and applies `research_area` (and a `methodology` facet where derivable) silently when the decision is clear — audited, never gated ([Ingest routing](../../reference/ingest.md)). What's left for you is the judgment the automation refuses to make:

- **Genuine ambiguity** — the engine left the field unset and raised one Inbox `flag` card with the top candidates and scores
- **The Librarian's proposal** — the `_proposed_classification` block on the paper entity, promoted by you
- **Corrections** — the automation applied something you disagree with; you edit the frontmatter, no card involved

## Prerequisites

- A paper ingested to `catalog/papers/<citekey>.md` ([Capture and ingest a source](capture-and-ingest.md))

## Steps

**1. Handle any classify `flag` card first.**

If ingest hit genuine ambiguity, a flag card titled along the lines of "Ambiguous research area for `<citekey>`" sits in your Inbox. It carries the `finding` and the scored candidates — never a verdict. Pick the right value, write it into the paper entity's frontmatter yourself, then resolve the card (`Cmd/Ctrl-P` → **Memoria: resolve inbox card**).

**2. Open the paper entity and review what the automation applied.**

In `catalog/papers/<citekey>.md`, check `research_area` and `methodology` against the paper itself. The thresholds (`classify.confidence_floor`, `classify.near_tie_margin`) live in `.memoria/schemas/calibration.yaml`; every applied or flagged decision is one JSONL line in `system/logs/classify.jsonl`. If a value is wrong, **edit the frontmatter directly** — the audit line is what makes the automation correctable; there is nothing to approve.

**3. Promote the `_proposed_classification` block.**

The Librarian's proposal (LLM hole #1) is a sandboxed namespace in the entity's frontmatter, separate from the main fields. Review each proposed value, copy the ones you accept (edited for accuracy) into the main frontmatter, then delete the entire `_proposed_classification:` block — it is transient.

**4. Flip the entity's lifecycle.**

A paper entity arrives at `lifecycle: proposed`. Once you've judged its candidate card and settled the classification, set it to `current`:

```yaml
lifecycle: current
```

**5. Carry the vocabulary into your source note.**

When you write the source note in `notes/source/`, reuse the same `research_area` / `methodology` terms — vocabulary drift between catalog and notes is what makes queries lie ([Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)).

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
