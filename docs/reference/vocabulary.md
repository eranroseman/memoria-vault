---
title: Vocabulary
parent: Reference
---

# Vocabulary

`system/vocabulary.md` is the visible, PI-editable home for the controlled values used by `research_area`, `methodology`, and claim `topics`.

The shipped file lives at [`src/system/vocabulary.md`](https://github.com/eranroseman/memoria-vault/blob/main/src/system/vocabulary.md). In a runtime vault, edit `system/vocabulary.md` directly and keep note frontmatter values in lockstep with it.

## Fields

| Field | Applies to | Source list |
| --- | --- | --- |
| `research_area` | `paper`, `source` | `system/vocabulary.md` → `## research_area` |
| `methodology` | `paper`, `source` | `system/vocabulary.md` → `## methodology` |
| `topics` | `claim` | Draw from `## research_area` so claims and sources stay queryable together |

## Related

- How to edit the lists: [Manage your topic vocabulary](../how-to-guides/curate/manage-vocabulary.md)
- Why this exists: [Vocabulary discipline](../explanation/knowledge/vocabulary-discipline.md)
- Frontmatter field grammar: [Frontmatter fields](frontmatter.md)
