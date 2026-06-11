---
topic: decisions
id: 06
title: Citekey naming convention
status: accepted
date_proposed: 2026-05-15
date_resolved: 2026-05-15
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 6
---

# ADR-06: Citekey naming convention

## Context

Citekeys are the load-bearing identifier for every paper-note (`@mamykina2010sense`). The Better BibTeX (BBT) format determines what gets generated; the convention determines whether the keys remain stable and readable across thousands of papers.

## Decision

Adopt **`authoryearword`** as the standard citekey format. Exact BBT format string (paste into Better BibTeX → Citation key formula):

```text
[auth.lower][year][shorttitle1_0]
```

This produces `mamykina2010sense` from a Mamykina 2010 paper titled "Sense and sensibility..." — surname lowercase, four-digit year, and the first significant title word via `shorttitle(1,0)` (one whole word, no fixed character count — do **not** substitute `condense:N`). **Pin the key in Zotero immediately after import** so subsequent metadata edits don't regenerate it.

## Consequences

- Keys are short, human-readable, and stable.
- Collisions are rare (different authors + same year + same title-word is uncommon); when they occur, BBT appends a disambiguator.
- The pin-immediately discipline is non-negotiable — without it, edits to Zotero metadata regenerate keys and break every wikilink pointing to the old key.

## Alternatives considered

**Stricter conventions** (e.g., full first-author surname + year + DOI suffix) were rejected because they sacrifice readability for marginal collision-resistance. The corpus's actual collision rate is well below the threshold that would justify the noise.

**Looser conventions** (e.g., year + arbitrary slug) were rejected because they lose the author-as-mnemonic property that makes citekeys readable in prose.

## Related

- **Workflows affected:** [Zotero capture](../how-to-guides/compile/capture-and-ingest.md), [Ingest](../reference/ingest.md)
- **Files affected:** [The vault](../explanation/architecture/vault.md), `system/templates/paper.md` (in the starter vault)
