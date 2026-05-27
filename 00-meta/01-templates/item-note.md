# `item-note` template

For repositories, packages, products, and standards. Lives in `20-sources/02-items/`. Umbrella type covering everything in the items folder.

## Frontmatter

```yaml
---
title: ""
type: item-note
item_category: repo                  # repo | package | product | standard
repo_url: ""
package_name: ""
vendor: ""
license: ""
triage_status: partial               # partial | full (matches source-note triage discipline)
maintenance_status: active           # active | deprecated | archived | unmaintained
role_in_stack: primary-tool          # primary-tool | dependency | alternative | reference-only
relevance_to_projects: []
maintainer: ""
last_checked:
moc: []
projects: []
schema_version: 1
created:
updated:
---
```

## Body

```md
# What it is
One-sentence description.

# Why it matters
- What problem it solves.
- Why you use it.
- Where it fits in the stack.

# Evaluation
- Strengths.
- Weaknesses.
- Alternatives.

# Usage notes
- Setup.
- Constraints.
- Integration details.
```

## Notes

`maintenance_status` is the item equivalent of a source note's `pub_status`. The linter's "stale items" check surfaces items whose `last_checked` is older than 90 days.

`role_in_stack` disambiguates how the item relates to your work. The four values:

- `primary-tool` — something you actively use day-to-day (e.g., Obsidian, Hermes, Zotero).
- `dependency` — something a primary tool depends on (e.g., Better BibTeX as a Zotero plugin).
- `alternative` — a tool you evaluated and chose not to use, kept for comparison and provenance.
- `reference-only` — a tool referenced in the literature but not part of your stack (e.g., a system you're studying but not running).

This field powers "show me my primary tools that haven't been re-enriched in 30 days" queries — the alternatives and reference-only items can decay quietly without urgency, but primary tools shouldn't.
