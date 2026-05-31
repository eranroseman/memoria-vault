# `claim-note` template

One durable claim, one note. Human-authored. Lives in `30-synthesis/01-claims/`. Promoted to `reference-note` (in `30-synthesis/02-reference/`) when `maturity: evergreen`.

## Frontmatter

```yaml
---
title: ""
type: claim-note
schema_version: 1
created:
updated:
maturity: seedling   # seedling → budding → evergreen
sources: []          # [[source notes]] this claim draws on — paper-note / item-note / entity in 20-sources/ (the source note, not a citekey)
moc: []
projects: []
lifecycle: current
superseded_by:       # [[newer-claim]] once overturned; currency derives from this field (ADR-22). Human-set.
relations:           # opt-in typed associative links (ADR-9). Human-set; the agent proposes only.
  supports: []       # [[claim]] this claim supports (directional)
  contradicts: []    # [[claim]] this claim disagrees with (symmetric)
---
```

## Maturity progression

- `seedling` — one source, claim newly drafted.
- `budding` — supported by multiple sources, linked from at least one other note.
- `evergreen` — stable, durable, ready for promotion to `30-synthesis/02-reference/`.

## Body

```md
# Claim
One durable claim in a single sentence.

# Evidence
- Why this claim seems true.
- Supporting sources.
- Important distinctions.

# Connections
- Related claim notes (untyped wikilinks).
- Contradictory and supporting claims are recorded as **typed links** in the `relations:` frontmatter (`contradicts` / `supports`), not just here — see [frontmatter-schema](../04-reference/schema-reference.md).
- Supporting paper notes.

# Open questions
- What remains unresolved.
- What would change this claim.
```
