---
title: Classify a source
parent: Compile
nav_order: 4
---


# Classify a source

When the Librarian ingests a paper it doesn't decide the final metadata — it only *proposes*. It writes its best guess into a sandboxed `_proposed_classification` block in the frontmatter and leaves the note at `lifecycle: proposed`.

**Classifying is the human step that turns that proposal into the note's real metadata.** You review each proposed field, copy the ones you accept (edited for accuracy) into the main frontmatter, delete the proposal block, and flip the note to `lifecycle: current`. No profile writes to the note while you do this — it's a deliberate checkpoint so the agent's guess never becomes canonical without your review.

The steps below are that loop: **review → promote → clean up → mark done.**

## Prerequisites

- The source has been ingested and is at `lifecycle: proposed` with a `_proposed_classification` block ([Capture and ingest a source](capture-and-ingest.md))

## Steps

**1. Open the note in Obsidian.**

Navigate to `20-sources/01-papers/<citekey>.md` (or `20-sources/02-items/<citekey>.md` for non-paper sources).

**2. Find the `_proposed_classification` block.**

It is an agent-owned namespace in the note's YAML frontmatter — a nested block the Librarian wrote, separate from the main (human-owned) fields:

```yaml
_proposed_classification:
  study_design: ...
  methods: [...]
  topic: [...]
```

`projects` is human-owned and is **not** proposed here — you set it yourself in step 4.

**3. Review each field.**

Compare the proposed values against the paper itself. The Librarian extracts these from the abstract and title — check for:

- **topic:** Is this the right concept vocabulary term? If the paper is about JITAI receptivity, `receptivity-detection` is correct; `jitai` alone is too broad.
- **methods:** Is `field-study` accurate, or was it also a `qualitative-interview` study? Add precision.
- **study_design:** `observational` vs. `experimental` — confirm from the methods section.

**4. Promote accepted fields to main frontmatter.**

Copy the fields you accept into the YAML frontmatter block at the top of the note. Edit for accuracy. Example:

```yaml
topic:
  - receptivity-detection
methods:
  - field-study
  - qualitative-interview
study_design: observational
projects:
  - jitai-timing
```

**5. Delete the `_proposed_classification` block.**

Remove the entire `_proposed_classification:` block from the frontmatter once you've promoted the fields you accept. The block is transient — it exists only until classification is complete.

**6. Set `lifecycle: current`.**

In frontmatter — this state *is* the "classified" marker (triage completion is tracked as a Kanban board state, not a note field):

```yaml
lifecycle: current
```

**7. Write a brief Key Findings entry.**

Scroll to the "Key findings" section in the note body. Write 2–3 sentences summarizing the paper's core contribution in your own words. This is the first place the note captures your thinking, not just the agent's extraction.

## Verify

- The note appears in the "classification complete" Dataview query on the `weekly-review.md` dashboard
- `lifecycle: current` is set and the `_proposed_classification` frontmatter block is gone
- The note does not appear in the "classification debt" queue on `weekly-review.md`

## Related

- Previous step: [Capture and ingest a source](capture-and-ingest.md)
- Next step: [Discuss a paper](discuss-a-paper.md)
- Frontmatter schema reference: [Frontmatter fields](../../reference/frontmatter.md)
- Vocabulary for `topic`, `methods`, `study_design`: [Frontmatter fields](../../reference/frontmatter.md#domain-fields)
