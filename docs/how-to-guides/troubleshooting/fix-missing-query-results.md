---
title: Fix missing query results
parent: Troubleshooting
grand_parent: How-to guides
nav_order: 10
---

# Fix missing query results

**Symptom:** a CLI/read-API query or optional editor view that filters on Work
`methodology`/`research_area` metadata or note `topics` returns nothing — or
quietly omits records you *know* should match. The Concepts are fine in every
other way: they open cleanly, show no YAML error, and appear in unfiltered
queries.

- A `topics` filter returns fewer notes than exist
- A Work metadata query misses Works with `research_area` or `methodology` values you expected
- A dashboard or hub view is emptier than the vault warrants
- The "missing" records are valid and visible everywhere except the filtered view

**Diagnosis:** the field value doesn't match the controlled vocabulary
*exactly*. Literal filters compare strings exactly, so a near-miss term (`RCT`
for `rct`, `field study` for `field-study`, a stray capital, a plural) silently
drops the record from the filtered result. The query engine does not error — the
value is well-formed, just off-vocabulary. Run the Linter's `schema-check` to
surface offending Concepts, and inspect Work metadata with `memoria work export`
or the read API ([Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)).

**Fix:** find the off-vocabulary values, then either correct the note to the exact controlled term or add the term to the vocabulary if it's genuinely new.

## First, rule out the two look-alike cases

This recipe is specifically for *structured* vocabulary filters. Two different
problems look similar:

| If… | It's not this — see |
| --- | --- |
| The note shows a YAML parse error, or is missing from **un**filtered queries too | [Fix broken frontmatter](fix-broken-frontmatter.md) |
| The **Co-PI** or semantic search misses notes (not a Dataview/Bases filter) | [Rebuild the search index](../operate/rebuild-the-search-index.md) |

If the record appears in an unfiltered query but vanishes the moment you filter
on a vocabulary field, you're in the right place.

## Detect

**1. List every note `topics` value actually in use.** Drop this into a scratch
note when using an optional editor — it surfaces the drift at a glance by
grouping notes under each distinct value:

```dataview
TABLE rows.file.link AS Notes
FROM "notes"
FLATTEN topics AS value
GROUP BY value
```

For Work `research_area` or `methodology`, inspect the Work through
`memoria work export --workspace . <work-id>` or the corresponding read API
payload instead of looking for source frontmatter.

**2. Compare the list against the controlled vocabulary.** Every value in the output should appear verbatim in [Vocabulary](../../reference/vocabulary.md) (the live list is `system/vocabulary.md`). Any value that *doesn't* — a variant spelling, wrong case, a space where there should be a hyphen, a term not in the list at all — is an offender, and the notes grouped under it are your missing notes.

## Fix

**1. Correct the record to the exact term.** Open each offending note and set
`topics` to the controlled value exactly — kebab-case, exact spelling, scalar vs
list as the schema requires ([Frontmatter fields](../../reference/frontmatter.md)).
For Work metadata, use `memoria work update`. The record re-appears once the
query source is refreshed.

**2. Or add the term to the vocabulary** — if the value is a legitimate concept the vocabulary simply lacks. Don't scatter one-off variants; promote it once, properly: [Manage vocabulary](../knowledge/manage-vocabulary.md). Then bring any existing variants into line with the new canonical term.

## Verify

- The original query now returns the previously-missing records
- Re-running the distinct-values query shows **only** controlled-vocabulary terms — no stragglers
- The dashboard or hub view that prompted this is no longer suspiciously empty

## If the fix doesn't hold

- **Case or whitespace.** `Field-Study` ≠ `field-study`; a trailing space defeats an exact match. Retype the value rather than edit in place.
- **Scalar vs list.** A field the schema expects as a list (`methodology: [field-study]`) won't match a scalar query and vice-versa — match the shape the query uses.
- **Wrong field.** Claim-bearing note subject tags live in `topics`; Work
  metadata uses `research_area` and `methodology`. Querying the wrong surface
  returns nothing even when every value is valid.
- **Stale Dataview cache.** If a corrected note still won't show, force a re-index (toggle the file, or reload Obsidian) — Dataview occasionally lags a rename.

## Related

- The controlled values: [Vocabulary](../../reference/vocabulary.md)
- Why the vocabulary is kept tight and how drift fails silently: [Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)
- Adding or consolidating a term: [Manage vocabulary](../knowledge/manage-vocabulary.md)
- The YAML-error look-alike: [Fix broken frontmatter](fix-broken-frontmatter.md)
- Full failure-modes catalog: [Failure modes](../../reference/failure-modes.md)
