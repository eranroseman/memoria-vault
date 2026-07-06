---
title: Wikilink and link conventions
parent: Vault data model
grand_parent: Reference
nav_order: 5
---

# Wikilink and link conventions

Alpha.15 has four knowledge Concept types: `work`, `note`, `hub`, and
`project`. Wikilinks and `links:` express authored PI relationships between
those Concepts. Catalog source/entity rows live in SQLite and provider payloads;
they are not `source`, `paper`, `person`, or `venue` Concept files.

---

## Link forms

| Form | Example | Meaning |
| --- | --- | --- |
| Body wikilink | `[[knowledge/notes/receptivity.md]]` | Plain human reference; never becomes an argument edge by itself. |
| Typed body shorthand | `[[supports::knowledge/notes/target.md]]` | Creates an unchecked edge-candidate attention item; the worker does not edit `links:` automatically. |
| Frontmatter `links:` | `supports: [knowledge/notes/target.md]` | Authored argument edge accepted into the Concept frontmatter. |
| Hub tag membership | `tags: [jitai]` with hub `tag: jitai` | Mechanical topic membership; the hub body owns curation and ordering. |

---

## Authored links

Knowledge Concepts carry `links:` as the authored relationship map specified by
[the four-type Concept model with meaning-only frontmatter](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md) and the generated
[Frontmatter fields](frontmatter.md). The only frontmatter link relations are:

| Link | Direction |
| --- | --- |
| `supports` | This Concept supports the linked Concept. |
| `contradicts` | This Concept contradicts the linked Concept. |
| `extends` | This Concept builds on the linked Concept. |

```yaml
links:
  supports:
    - knowledge/notes/target.md
  contradicts: []
  extends: []
```

Rules:

- Link for usefulness, not exhaustive coverage.
- Prefer vault-relative paths over title-only links.
- A `note` with `mode: claim` needs evidence in its body, anchors, or linked
  checked Works; `links:` records the argument relation, not the evidence store.
- A bare wikilink remains a body reference.
- A proposed machine edge is not canonical until accepted through the attention
  path.

Catalog/provider relationships such as citations, authors, venues, OpenAlex
related Works, and entity IDs live in SQLite records and provider payloads. They
are given facts from ingest/enrichment, not authored `links:` frontmatter.

---

## Expected topology

```text
work
  -> catalog Work row via work_id
  -> note/hub/project when the PI authors a local link

note
  -> work evidence in body text, anchors, and operation records
  -> note/hub/project through supports / contradicts / extends

hub
  -> tag-owned membership through checked Concept tags
  -> curated body links for featured paths and gaps

project
  -> one-way project -> corpus references
  -> thesis role through the project schema
  -> project exports under knowledge/projects/<project>/exports/
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
| `work` | `knowledge/works/<slug>.md` | `personal-informatics-sensemaking.md` |
| `note` | `knowledge/notes/<claim-or-question>.md` | `receptivity-decreases-under-high-burden.md` |
| `hub` | `knowledge/hubs/<topic>.md` | `jitai.md` |
| `project` | `knowledge/projects/<project>/project.md` | `knowledge/projects/dissertation/project.md` |

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
