---
title: "{{VALUE:claim title}}"
type: claim-note
schema_version: 1
created: {{DATE:YYYY-MM-DD}}
updated: {{DATE:YYYY-MM-DD}}
maturity: seedling
sources: []
moc: []
projects: []
lifecycle: current
superseded_by:
relations:
  supports: []
  contradicts: []
---

# Claim
One durable claim in a single sentence.

# Evidence
- Why this claim seems true.
- Supporting sources.
- Important distinctions.

# Connections
- Related claim notes (untyped wikilinks).
- Supporting paper notes.

> [!tip]- Recording contradictions & support
> Put contradictory/supporting claims in the `relations:` frontmatter (`contradicts` / `supports`), not just here — that's what the contradictions dashboard queries. See [frontmatter reference](https://eranroseman.github.io/memoria-vault/reference/frontmatter).

# Open questions
- What remains unresolved.
- What would change this claim.
