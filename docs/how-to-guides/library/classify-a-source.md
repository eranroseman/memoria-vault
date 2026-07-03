---
title: Classify a source
parent: Library
grand_parent: How-to guides
nav_order: 4
---

# Classify a source

Settle a Work's `research_area` and `topics` when ingest couldn't decide on its own.

Classifying tags a paper with its field of study. When a source comes in, ingest fills these tags in automatically wherever the answer is clear. Most of the time you do nothing. This guide covers the cases where the work lands on you.

Three situations bring you in:

| Situation | What it means |
| --- | --- |
| Genuine ambiguity | Ingest left the field blank and raised a `flag` attention item with candidate values and scores. It reports; you decide. |
| Draft to review | Attention carries suggested values separately from the catalog row. |
| Correction | Ingest applied a value you disagree with; update the Work row through the CLI. |

For what ingest decides and how, see [Ingest routing](../../reference/ingest.md).

## Prerequisites

- A captured Work ID from `memoria work add`, `memoria work import`, or `memoria work export` ([Capture and ingest a source](capture-and-ingest.md))

## Steps

**1. Handle any `flag` attention first.**

Use `memoria status`, `memoria request list`, or `memoria attention list` to find
source metadata attention. If ingest hit genuine ambiguity, you'll see a finding
for the Work. Pick the right value and update the catalog row:

```bash
memoria work update --workspace <vault> <work-id> --research-area <term>
```

Then resolve the attention item with `memoria attention resolve`.

**2. Export the Work and check what ingest applied.**

```bash
memoria work export --workspace <vault> <work-id>
```

Compare the catalog metadata against the source itself. If a value is wrong,
update it with `memoria work update`; the worker records the override in
`.memoria/overrides.jsonl` and the journal.

**3. Confirm the Work is checked/current.**

Classifying does not move files or create source frontmatter. Confirm the Work
still has checked DB/read-API state and current standing:

```bash
memoria work export --workspace <vault> <work-id>
```

If the exported row should be retired, use `--standing archived`, `--standing
retracted`, or `--standing superseded` deliberately.

**4. Reuse the same terms in notes and hubs.**

When you write checked notes or hubs from this source, use the same vocabulary.
Mismatched vocabulary between the catalog and knowledge graph is what makes
later queries miss results ([Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)).

## Verify

- The Work export reports settled metadata, `check_status: checked`, and current standing
- No `flag` attention item for this citekey is still open in your queue
- `.memoria/overrides.jsonl` and the journal record any PI override for this Work

## Related

- Previous step: [Capture and ingest a source](capture-and-ingest.md)
- Next step: [Discuss a paper](discuss-a-paper.md)
- The automation's thresholds and audit trail: [Ingest routing](../../reference/ingest.md)
- Field semantics: [Frontmatter fields](../../reference/frontmatter.md)
- Optional per-project hints the proposal draws on: [Configure project hints](../setup/configure-project-hints.md)
