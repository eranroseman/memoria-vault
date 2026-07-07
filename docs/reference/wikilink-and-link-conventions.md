---
title: Wikilink and link conventions
parent: Reference
nav_order: 5
---

# Wikilink and link conventions

Alpha.19 has file-backed document types for `digest`, `fulltext`, `note`,
`hub`, and `project`. Wikilinks and `links:` express authored PI relationships
between Concept documents. Catalog Work rows live in SQLite and provider
payloads; they are not `paper`, `person`, or `venue` Concept files.

---

## Link forms

| Form | Example | Meaning |
| --- | --- | --- |
| Body wikilink | `[[notes/receptivity.md]]` | Plain human reference; never becomes an argument edge by itself. |
| Typed body shorthand | `[[supports::notes/target.md]]` | Creates an unchecked edge-candidate attention item; the worker does not edit `links:` automatically. |
| Frontmatter `links:` | `supports: [notes/target.md]` | Authored argument edge accepted into the Concept frontmatter. |
| Hub tag membership | `tags: [jitai]` with hub `tag: jitai` | Mechanical topic membership; the hub body owns curation and ordering. |

---

## Authored links

Knowledge Concepts carry `links:` as the authored relationship map specified by
the generated [Frontmatter fields](frontmatter.md). The only frontmatter link
relations are:

| Link | Direction |
| --- | --- |
| `supports` | This Concept supports the linked Concept. |
| `contradicts` | This Concept contradicts the linked Concept. |
| `extends` | This Concept builds on the linked Concept. |

```yaml
links:
  supports:
    - notes/target.md
  contradicts: []
  extends: []
```

Rules:

- Link for usefulness, not exhaustive coverage.
- Prefer vault-relative paths over title-only links.
- A `note` with `mode: claim` needs evidence in its body, anchors, checked
  digests, or catalog Work rows; `links:` records the argument relation, not
  the evidence store.
- A bare wikilink remains a body reference.
- A proposed machine edge is not canonical until accepted through the attention
  path.

Catalog/provider relationships such as citations, authors, venues, OpenAlex
related Works, and entity IDs live in SQLite records and provider payloads. They
are given facts from ingest/enrichment, not authored `links:` frontmatter.

---

## Expected topology

```text
digest/fulltext
  -> catalog Work row via work_id
  -> note/hub/project when the PI authors a local link

note
  -> source evidence in body text, anchors, digests, and operation records
  -> note/hub/project through supports / contradicts / extends

hub
  -> tag-owned membership through checked Concept tags
  -> curated body links for featured paths and gaps

project
  -> one-way project -> corpus references
  -> thesis role through the project schema
  -> project exports under projects/<project>/exports/
```

---

## Hub thresholds

The `hub-threshold` linter detector is advisory. When a topic has roughly 15 or
more checked notes and no covering hub, create a `hub` Concept with one owned
tag. Below that, the missing hub is usually cheaper than maintaining a premature
navigation page.

---

## Slug conventions

| Concept | Path shape | Example |
| --- | --- | --- |
| catalog work | `catalog/sources/<work-id>` | `catalog/sources/personal-informatics-sensemaking` |
| `digest` | `digests/<work-id>.md` | `digests/personal-informatics-sensemaking.md` |
| `fulltext` | `fulltexts/<work-id>.md` | `fulltexts/personal-informatics-sensemaking.md` |
| `note` | `notes/<claim-or-question>.md` | `receptivity-decreases-under-high-burden.md` |
| `hub` | `hubs/<topic>.md` | `jitai.md` |
| `project` | `projects/<project>/project.md` | `projects/dissertation/project.md` |

The stable identity is the ULID `id`, not the filename. Renames are still rare:
they churn links and require a scan/check pass.

---

## Vocabulary discipline

The `research_area`, `methodology`, and topic tags use the controlled lists in
[Vocabulary](vocabulary.md), whose runtime home is `system/vocabulary.md`.
Richer provider taxonomies such as OpenAlex topics are catalog metadata, not
hand-authored frontmatter vocabulary.

---

## Related

- How-to for setting authored links: [Link checked notes](../how-to-guides/knowledge/link-checked-notes.md)
- Field contract: [Frontmatter fields](frontmatter.md)
- Current Concept types: [Document types](document-types.md)
- Why notes are filed by lifecycle, not topic: [Lifecycle, not topic — and state, not folders](../design/lifecycle-over-topic.md)
