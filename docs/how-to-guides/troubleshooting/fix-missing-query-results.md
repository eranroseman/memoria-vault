---
title: Fix missing query results
parent: Troubleshooting
grand_parent: How-to guides
nav_order: 6
---

# Fix missing query results

**Symptom:** an optional third-party editor view that filters on Work
`methodology`/`research_area` metadata or note `topics` returns nothing — or
quietly omits records you *know* should match. The Concepts are fine in every
other way: they open cleanly, show no YAML error, and appear in the view's
unfiltered results.

- A `topics` filter returns fewer notes than exist
- An optional Work-metadata view misses Works with `research_area` or `methodology` values you expected
- A dashboard or hub view is emptier than the vault warrants
- The "missing" records are valid and visible everywhere except the filtered view

**Diagnosis:** the editor view's field filter may not match the stored value or
field shape exactly. Literal third-party filters commonly compare strings
exactly, so a near-miss term (`RCT` for `rct`, `field study` for `field-study`,
a stray capital, a plural) can silently drop a record. Run the Linter's
`schema-check` for claim-note `topics`, then inspect the Work metadata with
`memoria work export` ([Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)).

The shipped CLI and read API do not yet offer structured filters for Work
classifications or note topics. This guide applies only to optional
third-party-editor views you configure yourself.

**Fix:** find the off-vocabulary values, then either correct the note to the exact controlled term or add the term to the vocabulary if it's genuinely new.

## First, rule out the two look-alike cases

This recipe is specifically for *third-party editor* field filters. Two different
problems look similar:

| If… | It's not this — see |
| --- | --- |
| The note shows a YAML parse error, or is missing from the editor view's **un**filtered results too | [Fix broken frontmatter](fix-broken-frontmatter.md) |
| The **Co-PI** or semantic search misses notes, not a filtered editor view | [Rebuild the search index](../operate/rebuild-the-search-index.md) |

If the record appears in the editor view's unfiltered results but vanishes the moment you filter
on a vocabulary field, you're in the right place.

## Detect

**1. List every note `topics` value actually in use.** Run the Linter's
`schema-check` first. If you installed Dataview in Obsidian yourself, this
scratch query can also surface drift by grouping notes under each distinct
value:

```dataview
TABLE rows.file.link AS Notes
FROM "notes"
FLATTEN topics AS value
GROUP BY value
```

For Work `research_area` or `methodology`, inspect the Work through
`memoria work export --workspace <workspace> <work-id>` instead of looking for
source frontmatter.

**2. Compare note topics against the controlled vocabulary.** Every `topics`
value in the output should appear verbatim in [Vocabulary](../../reference/data-model/vocabulary.md)
(the live list is `system/vocabulary.md`). Any value that does not is an
offender, and the notes grouped under it are your missing notes. Work
classifications are PI-controlled guidance rather than schema-enforced values;
compare their spelling and shape with the view's own filter configuration.

## Fix

**1. Correct the record to the exact term.** Open each offending note and set
`topics` to the controlled value exactly — kebab-case, exact spelling, scalar vs
list as the schema requires ([Frontmatter fields](../../reference/data-model/frontmatter.md)).
For Work metadata, use `memoria work update --workspace <workspace> <work-id>
--research-area <term>` or `--methodology <term>`. Both flags are repeatable.
Refresh the third-party view after editing. Work has no `topics` field; note
`topics` draw from the `research_area` list instead.

**2. Or add the term to the vocabulary** — if the value is a legitimate concept the vocabulary lacks. Don't scatter one-off variants; promote it once, properly: [Manage vocabulary](../knowledge/manage-vocabulary.md). Then bring any existing variants into line with the new canonical term.

## Verify

- The original third-party editor view now returns the previously-missing records
- Re-running the distinct-values query shows **only** controlled-vocabulary terms — no stragglers
- The dashboard or hub view that prompted this is no longer suspiciously empty

## If the fix doesn't hold

- **Case or whitespace.** `Field-Study` ≠ `field-study`; a trailing space defeats an exact match. Retype the value rather than edit in place.
- **Scalar vs list.** Match the field shape the third-party view expects.
- **Wrong field.** Claim-bearing note subject tags live in `topics`; Work
  metadata uses `research_area` and `methodology`. Querying the wrong surface
  returns nothing even when every value is valid.
- **Stale optional-editor cache.** If a corrected note still won't show in an
  editor view, force that plugin to re-index or reload Obsidian.

## Related

- The controlled values: [Vocabulary](../../reference/data-model/vocabulary.md)
- Why the vocabulary is kept tight and how drift fails silently: [Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)
- Adding or consolidating a term: [Manage vocabulary](../knowledge/manage-vocabulary.md)
- The YAML-error look-alike: [Fix broken frontmatter](fix-broken-frontmatter.md)
- Full failure-modes catalog: [Failure modes](../../reference/system/failure-modes.md)
