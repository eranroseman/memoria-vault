---
title: Fix missing query results
parent: Troubleshooting
grand_parent: How-to guides
nav_order: 10
---

# Fix missing query results

**Symptom:** a Dataview or Bases view that filters on `methodology`, `research_area`, or claim `topics` returns nothing — or quietly omits notes you *know* should match. The notes are fine in every other way: they open cleanly, show no YAML error, and appear in unfiltered queries.

- A `WHERE methodology = "..."` (or a Base filter on the field) returns fewer notes than exist
- A dashboard or hub view is emptier than the vault warrants
- The "missing" notes are valid and visible everywhere except the filtered view

**Diagnosis:** the field value doesn't match the controlled vocabulary *exactly*. Dataview and Bases compare strings literally, so a near-miss term (`RCT` for `rct`, `field study` for `field-study`, a stray capital, a plural) silently drops the note from the filtered result. The query engine does not error — the value is well-formed YAML, just off-vocabulary. Run the Linter's `schema-check` to surface the offending note ([Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)).

**Fix:** find the off-vocabulary values, then either correct the note to the exact controlled term or add the term to the vocabulary if it's genuinely new.

## First, rule out the two look-alike cases

This recipe is specifically for *structured* queries (Dataview / Bases filtering on a vocabulary field). Two different problems look similar:

| If… | It's not this — see |
| --- | --- |
| The note shows a YAML parse error, or is missing from **un**filtered queries too | [Fix broken frontmatter](fix-broken-frontmatter.md) |
| The **Co-PI** or semantic search misses notes (not a Dataview/Bases filter) | [Rebuild the search index](../operate/rebuild-the-search-index.md) |

If the note appears in an unfiltered query but vanishes the moment you filter on a vocabulary field, you're in the right place.

## Detect

**1. List every value actually in use for the field.** Drop this into a scratch note — it surfaces the drift at a glance by grouping notes under each distinct value:

```dataview
TABLE rows.file.link AS Notes
FROM "notes" OR "catalog"
FLATTEN methodology AS value
GROUP BY value
```

Swap `methodology` for `research_area` or `topics` as needed.

**2. Compare the list against the controlled vocabulary.** Every value in the output should appear verbatim in [Vocabulary](../../reference/vocabulary.md) (the live list is `system/vocabulary.md`). Any value that *doesn't* — a variant spelling, wrong case, a space where there should be a hyphen, a term not in the list at all — is an offender, and the notes grouped under it are your missing notes.

## Fix

**1. Correct the note to the exact term.** Open each offending note and set the field to the controlled value exactly — kebab-case, exact spelling, scalar vs list as the schema requires ([Frontmatter fields](../../reference/frontmatter.md)). The note re-appears in the view within a few seconds (Dataview re-indexes on save).

**2. Or add the term to the vocabulary** — if the value is a legitimate concept the vocabulary simply lacks. Don't scatter one-off variants; promote it once, properly: [Manage vocabulary](../knowledge/manage-vocabulary.md). Then bring any existing variants into line with the new canonical term.

## Verify

- The original query now returns the previously-missing notes
- Re-running the distinct-values query shows **only** controlled-vocabulary terms — no stragglers
- The dashboard or hub view that prompted this is no longer suspiciously empty

## If the fix doesn't hold

- **Case or whitespace.** `Field-Study` ≠ `field-study`; a trailing space defeats an exact match. Retype the value rather than edit in place.
- **Scalar vs list.** A field the schema expects as a list (`methodology: [field-study]`) won't match a scalar query and vice-versa — match the shape the query uses.
- **Wrong field.** Claim subject tags live in `topics`, not `research_area`; querying the wrong field returns nothing even when every value is valid.
- **Stale Dataview cache.** If a corrected note still won't show, force a re-index (toggle the file, or reload Obsidian) — Dataview occasionally lags a rename.

## Related

- The controlled values: [Vocabulary](../../reference/vocabulary.md)
- Why the vocabulary is kept tight and how drift fails silently: [Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)
- Adding or consolidating a term: [Manage vocabulary](../knowledge/manage-vocabulary.md)
- The YAML-error look-alike: [Fix broken frontmatter](fix-broken-frontmatter.md)
- Full failure-modes catalog: [Failure modes](../../reference/failure-modes.md)
