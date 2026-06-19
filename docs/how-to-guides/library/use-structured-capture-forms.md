---
title: Use structured capture forms
parent: Library
nav_order: 3
---

# Use structured capture forms

Stage a source from a guided form when you're entering its metadata by hand — a report, a web page, a dataset, or a paper you want to log without running the enrichment pipeline. The **structured source capture** form (a Modal Forms form, [ADR-71](../../adr/71-structured-capture-forms.md)) collects schema-valid fields and writes a proper `source` note plus an Inbox candidate, so a hand-entered source still arrives shaped like every other one.

This guide covers the **source-capture** form specifically. The project on-ramp form is a different surface — see [Start a writing project](../project/start-a-writing-project.md).

## When to use the form

Pick the capture route by what you have:

| You have… | Use | Why |
| --- | --- | --- |
| A paper with a resolvable DOI or a Zotero/BibTeX citekey | **Capture from URL / Zotero** | Runs the full deterministic ingest — enrichment, classification, links ([Capture and ingest a source](capture-and-ingest.md)). |
| A source you'll describe by hand — report, web page, dataset, or a paper to log without enrichment | **Structured source capture** (this guide) | A guided form with schema-valid fields; no DOI required, no enrichment pipeline. |

## Prerequisites

- The `modalforms` plugin enabled (it ships with the vault — [Obsidian plugins](../../reference/obsidian-plugins.md)); the command no-ops with a notice if the Modal Forms API isn't available

## Steps

**1. Open the form.**

`Cmd/Ctrl-P` → **Memoria: structured source capture**.

**2. Fill the fields.**

| Field | Required | Notes |
| --- | --- | --- |
| Source title | yes | Becomes the note title and the candidate-card title. |
| Catalog entity | yes | A note picker over `catalog/` — link the source to its Catalog entity. |
| Source type | yes | `paper` · `dataset` · `repository` · `web-page` · `report`. |
| Evidence level | no | CEBM 1–5 or `ungraded`. |
| Research area | no | From the controlled vocabulary ([Vocabulary](../../reference/vocabulary.md)). |
| Methodology | no | From the controlled vocabulary. |
| Summary | no | Your-words summary — what it claims, on what evidence. |

Title and catalog entity are enforced; submit without them and the form re-prompts.

**3. Submit.**

The form stages two files: a `source` note at `lifecycle: proposed` under `notes/sources/` (with `# In my words`, `# Worth distilling`, and `# Tensions` sections, and a button to create a linked claim), and an Inbox `candidate` card pointing at it (`raised_by: modalforms`, `loudness: notice`). A success notice names both paths. The note is staging — it is not a canonical claim or hub write.

**4. Judge the candidate.**

Open the Inbox space's **Needs me** view and resolve the card: keep the source (resolve to `current`) or archive it. Resolving is one palette command — [Work the review queue](../inbox/work-the-review-queue.md).

## Verify

- `notes/sources/<title-slug>.md` exists at `lifecycle: proposed` with `type: source` and the `entity:` wikilink you chose
- An `inbox/candidate-structured-source-<slug>.md` card landed, pointing at the staged note
- The note's `research_area` / `methodology` values match the controlled vocabulary exactly (off-vocabulary values silently drop from filtered views — [Fix missing query results](../troubleshooting/fix-missing-query-results.md))

## Related

- The enriched capture path for papers with a DOI/citekey: [Capture and ingest a source](capture-and-ingest.md)
- The palette command behind the form: [Obsidian command palette](../../reference/obsidian-command-palette.md)
- The `source` note schema: [Frontmatter fields](../../reference/frontmatter.md), [Note types](../../reference/note-types.md)
- Resolving the candidate it raises: [Work the review queue](../inbox/work-the-review-queue.md)
- The decision: [ADR-71: Structured capture forms](../../adr/71-structured-capture-forms.md)
