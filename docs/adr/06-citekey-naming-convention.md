---
topic: decisions
id: 06
title: Citekey naming convention
nav_exclude: true
status: accepted
date_proposed: 2026-05-15
date_resolved: 2026-05-15
assumes: []
supersedes: []
superseded_by: []
---

# ADR-06: Citekey naming convention

## Context

Citekeys are human-facing aliases for Works (`@mamykina2010sense`). Stable Work
IDs and provider identifiers are the runtime keys; citekeys stay useful because
they are readable in prose, exports, and imported BibTeX/CSL metadata.

## Decision

Adopt **`authoryearword`** as the standard citekey shape. Zotero/Better BibTeX
users can produce it with this formula:

```text
[auth.lower][year][shorttitle1_0]
```

This produces `mamykina2010sense` from a Mamykina 2010 paper titled "Sense and sensibility..." — surname lowercase, four-digit year, and the first significant title word via `shorttitle(1,0)` (one whole word, no fixed character count — do **not** substitute `condense:N`). If Zotero is used, pin the key before exporting so later metadata edits do not change the alias.

## Consequences

- Keys are short, human-readable, and stable.
- Collisions are rare (different authors + same year + same title-word is uncommon); when they occur, BBT appends a disambiguator.
- Zotero users pin keys before export; non-Zotero imports can supply the same shape directly.

## Alternatives considered

**Stricter conventions** (e.g., full first-author surname + year + DOI suffix) were rejected because they sacrifice readability for marginal collision-resistance. The corpus's actual collision rate is well below the threshold that would justify the noise.

**Looser conventions** (e.g., year + arbitrary slug) were rejected because they lose the author-as-mnemonic property that makes citekeys readable in prose.

## Related

- **Workflows affected:** [Capture and ingest](../how-to-guides/library/capture-and-ingest.md), [Ingest](../reference/ingest.md)
- **Authority:** [ADR-124 standalone catalog citation authority](124-standalone-catalog-citation-authority.md)
