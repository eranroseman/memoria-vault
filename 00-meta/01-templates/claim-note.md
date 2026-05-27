# `claim-note` template

One durable claim, one note. Human-authored. Lives in `30-synthesis/01-permanent/`. Promoted to `reference-note` (in `30-synthesis/02-wiki/`) when `maturity: evergreen`.

## Frontmatter

```yaml
---
title: ""
type: claim-note
schema_version: 1
created:
updated:
maturity: seedling   # seedling → budding → evergreen
sources: []
moc: []
projects: []
tags: []
status: active
---
```

## Maturity progression

- `seedling` — one source, claim newly drafted.
- `budding` — supported by multiple sources, linked from at least one other note.
- `evergreen` — stable, durable, ready for promotion to `30-synthesis/02-wiki/`.

## Body

```md
# Claim
One durable claim in a single sentence.

# Evidence
- Why this claim seems true.
- Supporting sources.
- Important distinctions.

# Connections
- Related claim notes.
- Contradictory claim notes.
- Supporting source notes.

# Open questions
- What remains unresolved.
- What would change this claim.
```
