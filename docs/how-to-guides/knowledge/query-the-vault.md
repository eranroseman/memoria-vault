---
title: Query the vault
parent: Knowledge
grand_parent: How-to guides
nav_order: 7
---

# Query the vault

Ask a grounded question over checked workspace knowledge with `memoria ask`.

## Which retrieval path?

| You want | Use | Output |
| --- | --- | --- |
| A synthesized answer grounded in checked knowledge | `memoria ask` | CLI answer with sources and unknowns |
| A project-scoped question | `memoria project ask <project-id>` | Same answer contract plus checked project context |
| Project-specific missing evidence | `memoria project gaps <project-id>` | gap report |
| Durable synthesis to keep | `memoria work digest` or `memoria note propose` | checked or candidate Markdown output |
| Fast exact lookup | editor search or `rg` | matching files |

## Prerequisites

- Checked sources, digests, or notes in the workspace.
- Current qmd index. Rebuild it if results look stale: [Rebuild the search index](../operate/rebuild-the-search-index.md).

## Steps

**1. Ask in natural language.**

```bash
memoria ask --workspace . --question "What predicts JITAI receptivity?"
memoria ask --workspace . --question "Which checked claims would the 2024 papers contradict?"
memoria ask --workspace . --question "What methods have my sources used to measure EMA compliance?"
memoria project ask project-alpha --workspace . --question "What matters for this project?"
```

**2. Inspect sources and unknowns.**

The answer is read-only. It should name the checked sources it used and state
unknowns when the checked corpus does not support an answer.

`memoria project ask` also uses the checked project's scope/facet terms and
checked linked thesis terms as retrieval context. Keep project frontmatter
current when project-scoped answers feel too broad or too narrow.

**3. Keep durable insights deliberately.**

If an answer is worth keeping, write or curate it through the normal workspace
flow:

```bash
memoria note propose --workspace . --work-id <work-id>
memoria workspace scan --workspace .
```

## Verify

- Every kept assertion traces to a checked source, digest, or note.
- Unchecked or quarantined files were not used as evidence.
- Anything durable exists as a note, digest, project update, or request outcome recorded in the journal.

## Related

- Search engine: [Search](../../reference/search.md)
- Rebuild the search index: [Rebuild the search index](../operate/rebuild-the-search-index.md)
- System actions: [System actions](../../reference/system-actions.md)
