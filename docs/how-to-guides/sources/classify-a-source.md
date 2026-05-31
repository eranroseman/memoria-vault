
# How to classify a source

Promote the Librarian's proposed classification into the note's canonical metadata and mark the source as reviewed. This is a human-only step — no profile touches the note during classification.

## Prerequisites

- The source has been ingested and is at `lifecycle: proposed` with a `_proposed_classification` block ([capture-and-ingest.md](capture-and-ingest.md))

## Steps

**1. Open the note in Obsidian.**

Navigate to `20-sources/01-papers/<citekey>.md` (or `20-sources/02-items/<citekey>.md` for non-paper sources).

**2. Find the `_proposed_classification` block.**

It appears as an HTML comment below the frontmatter, containing:

```text
<!-- _proposed_classification
study_design: ...
methods: [...]
topic: [...]
projects: [...]
-->
```

**3. Review each field.**

Compare the proposed values against the paper itself. The Librarian extracts these from the abstract and title — check for:

- **topic:** Is this the right concept vocabulary term? If the paper is about JITAI receptivity, `receptivity-detection` is correct; `jitai` alone is too broad.
- **methods:** Is `field-study` accurate, or was it also a `qualitative-interview` study? Add precision.
- **study_design:** `observational` vs. `experimental` — confirm from the methods section.
- **projects:** Which active project does this feed? Add or remove as appropriate.

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

Remove the entire `<!-- _proposed_classification ... -->` comment from the file.

**6. Set `lifecycle: current` and `triage_completed`.**

In frontmatter:

```yaml
lifecycle: current
triage_completed: 2026-05-31
```

**7. Write a brief Key Findings entry.**

Scroll to the "Key findings" section in the note body. Write 2–3 sentences summarizing the paper's core contribution in your own words. This is the first place the note captures your thinking, not just the agent's extraction.

## Verify

- The note appears in the "classification complete" Dataview query on the `weekly-review.md` dashboard
- `lifecycle: current` is set and `_proposed_classification` is gone
- The note does not appear in the "classification debt" queue on `weekly-review.md`

## Related

- Previous step: [Capture and ingest a source](capture-and-ingest.md)
- Next step: [Discuss a paper](discuss-a-paper.md)
- Frontmatter schema reference: [reference/frontmatter-schema.md](../../reference/frontmatter.md)
- Vocabulary for `topic`, `methods`, `study_design`: [reference/frontmatter-schema.md](../../reference/frontmatter.md)
