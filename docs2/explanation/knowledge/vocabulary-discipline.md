# Vocabulary discipline

How to build and maintain the three classification fields that make your vault Dataview-queryable at scale.

## The three fields and why they're separate

Memoria uses three distinct tagging fields. Mixing them in a single field makes all three query types unreliable:

| Field | What it captures | Example values | Cardinality |
| --- | --- | --- | --- |
| `study_design` | Research architecture — *how* the study was structured | `rct`, `design-science`, `qualitative`, `meta-analysis` | One value per note |
| `methods` | Specific techniques used | `ema`, `jitai`, `semi-structured-interview` | List; multiple per note |
| `topic` | Conceptual content — *what* the work is about | `receptivity-detection`, `health-coaching`, `sensemaking` | List; multiple per note |

If you put `receptivity-detection` in `study_design`, the query "show me all RCTs" fails. If you put `qualitative` in `topic`, the query "show me everything on sensemaking" returns noise. The fields answer different questions and must stay separated.

## Free-tag first, consolidate later

**Weeks 1–50 papers:** Use whatever terms come naturally when classifying. Write `opportune-moment` if that's how you're thinking; write `receptivity` if that feels right. Don't force consistency yet. The goal at this stage is to get notes into the system, not to enforce vocabulary.

**At 50 papers:** Review the full set of terms you've used. Run a Dataview query to surface all unique topic values across the vault. Consolidate: pick one term for each concept, update the notes that used alternative spellings or synonyms. This consolidation is the first time you're actually building vocabulary.

**Ongoing:** Keep the active `topic` vocabulary to approximately 30 terms. A smaller vocabulary produces more consistent classification and more useful queries. When a new term genuinely doesn't fit any existing term, add it; when two terms are always co-occurring, merge them.

**Reference taxonomies belong in `_enrichment`, not in `topic`.** MeSH terms, ACM CCS concepts, and OpenAlex concepts are auto-populated by the Librarian and useful for reference, but they are too granular and inconsistently applied across databases to use as Dataview query targets. Your custom `topic` vocabulary is what you query; the API taxonomies are what you browse.

## Vocabulary drift and how it fails silently

The most common vocabulary failure: you classify paper A with `topic: receptivity-detection` and paper B with `topic: opportune-moments`, not noticing they're the same concept. The dashboard query `WHERE contains(topic, "receptivity-detection")` then shows half your corpus on the topic, and you conclude coverage is thin when it isn't.

The Linter's `schema-check` detector validates that field values match the defined vocabulary. But the vocabulary must be defined first — the Linter can only catch drift from what you've said is canonical.

Practical check: before classifying a new paper, search the vault for existing uses of the term you're about to use (`Cmd+P → Omnisearch → the term`). If you find notes using it slightly differently, standardize before adding.

## When to promote to the schema reference

Once a term has appeared on 5+ notes, add it to `00-meta/04-reference/schema-reference.md` (the human-facing in-vault reference) and to the vocabulary tables in [reference/frontmatter.md](../../reference/frontmatter.md). Before it reaches 5 notes, it's provisional; after, it's part of the vocabulary contract the Linter enforces.

## study_design controlled vocabulary

Twelve values cover most research in HCI and digital health. Use exactly these strings for Dataview consistency:

```
rct                   controlled-experiment   quasi-experimental
observational         systematic-review       meta-analysis
qualitative           mixed-methods           design-science
technical             theoretical             secondary-analysis
```

If a paper doesn't fit any of these, use `other` and add a note in the `methods` field.
