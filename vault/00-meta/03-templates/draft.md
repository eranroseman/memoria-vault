# `draft` template

Manuscript or chapter in progress. Lives in `40-workbench/*/04-drafts/`. Human-authored. Promoted to `deliverable` on export.

## Frontmatter

```yaml
---
title: ""
type: draft
lifecycle: proposed        # proposed (outline, in-progress) | current (submitted)
draft_stage: in-progress   # outline | in-progress | submitted
project: ""
chapter: ""
target_venue: ""
related_notes: []
related_sources: []
schema_version: 1
created:
updated:
---
```

## Body

```md
# Outline
- Section 1
- Section 2
- Section 3

# Draft text

Prose. Use citekey links inline: [[mamykina2010sense]]. Pandoc handles citation rendering on export.

# Open questions
- Things still to resolve before export.
```

## Notes

- Drafts are not canonical notes — they're working manuscripts. The agent assists only on explicit request.
- Use Pandoc citekeys (`[@citekey]`) for inline citations during drafting; the export pipeline resolves them via `.memoria/library.bib`.
