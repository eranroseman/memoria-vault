---
title: Wikilink and link conventions
parent: Reference
---

# Wikilink and link conventions

Wikilink conventions, typed-relation vocabulary, cross-link topology, and MOC creation thresholds — the *how*. The *why* linking is load-bearing isn't a single page; it's explained across the knowledge model: why connections are a required section ([Note body structure](../explanation/knowledge/note-body-structure.md)), why topics live in links rather than folders ([Lifecycle, not topic — and state, not folders](../explanation/knowledge/lifecycle-over-topic.md)), and why a densely linked vault compounds ([The knowledge cycle](../explanation/knowledge/knowledge-cycle.md)). For the overall conceptual model see [explanation/vault](../explanation/architecture/vault.md).

---

## Link types

| Type | Syntax | Direction | Use |
| --- | --- | --- | --- |
| `citekey-link` | `[[mamykina2010sense]]` | `claim` → `paper` | Link a claim to its supporting paper. |
| `concept-link` | `[[receptivity-decreases-under-high-cognitive-load]]` | `claim` ↔ `claim` | Connect related claims; builds the knowledge graph. |
| `hub-link` | `[[jitai-design-hub]]` | Note → `hub` | Place a note within a navigational hub. |
| `entity-link` | `[[mamykina-lena]]` | Any → catalog entity | Connect people, organizations, venues, datasets, repositories. |
| `agent-cross-link` | Inline in note body | Proposed | Agent-generated candidates; human confirms before treating as canonical. |

---

## Linking rules

- Link for usefulness, not completeness.
- Every `claim` must trace to at least one `paper` citekey.
- Every `paper` should eventually connect to at least one relevant `hub`.
- Use concept links only when the relationship would matter in a later reading or writing session.
- Prefer one strong hub link over many weak generic links.
- Provenance direction: claims point to evidence; do not link the other way.
- Never treat an agent-proposed cross-link as canonical until reviewed.
- An orphan note must receive a hub link or relevant concept links before it is considered complete.
- Do not link a `paper` to a `claim` as if they were peers; the claim stands on its own and the paper is its support.

---

## Required patterns by type

| Note type | Required link structure |
| --- | --- |
| `paper` | `relationships:` frontmatter on the Catalog entity (`cited_by`, `authored_by`, `published_in`) — given facts from the bibliographic record. |
| `claim` | `sources:` frontmatter listing the citekey(s) the claim draws on. `Connections` section for conceptual neighbors via authored `links:`. |
| `hub` | `links:` frontmatter. Body: overview, curated entries, gaps. |

---

## Authored links (`links:` map)

Notes carry **authored** `links:` — the PI's thinking ([ADR-52](../adr/52-links-vs-relationships.md)). Available on `source`, `claim`, and `hub` notes; agent-proposed candidates are reviewed before they become canonical.

```yaml
links:
  supports:
    - "[[another-claim]]"
  contradicts:
    - "[[a-conflicting-claim]]"
  extends:
    - "[[a-foundational-claim]]"
```

Allowed link types:

| Link | Direction |
| --- | --- |
| `supports` | This note supports the linked note. |
| `contradicts` | This note contradicts the linked note. |
| `extends` | This note builds on the linked note. |

Catalog entities carry **given** `relationships:` instead — `cited_by`, `authored_by`, `published_in` — facts from the bibliographic record, written by the ingest engine. Adding a new authored link type requires updating this reference and the Linter's `frontmatter-link` detector.

---

## Cross-link topology

Expected link graph by note type:

```text
paper ({citekey})
  ↔ person               (authored_by)
  ↔ venue                (published_in)
  ↔ organization         (author affiliation)
  ↔ paper (other)        (cited_by)

claim
  → paper                (citekey in sources:)
  ↔ claim (other)        (authored links — supports / contradicts / extends)
  → hub                  (links: frontmatter)

person
  ↔ paper                (authored)
  ↔ organization         (affiliated with)

organization
  ↔ person               (members, affiliates)
  ↔ venue                (hosts or sponsors)

venue
  ↔ paper                (published)

hub
  ← claim                (links: frontmatter on claims)
  ← paper                (links: frontmatter on sources)
  ↔ hub (other)          (parent/child hub hierarchy)

project
  ← project artifacts    (projects/<project>/* all reference the project note)
```

---

## Hub thresholds

| Threshold | Action |
| --- | --- |
| ≥ 15–20 notes (papers + claims combined) on a topic | Create a top-level hub for the topic. |
| > 20 claims + > 10 papers on a branch | Build a child hub for that branch. |

Do not create a hub before these thresholds. Below the threshold, live with the lack of a hub — the friction is lower than the cost of maintaining a premature hub.

---

## Vocabulary discipline

The `research_area`, `methodology`, and `topics` fields are open — Memoria does not enforce a controlled vocabulary. Guidelines:

- Keep the active `topics` list to **~30 terms** per corpus. A smaller vocabulary produces more consistent classification.
- Richer taxonomy (MeSH, ACM CCS, OpenAlex concepts) belongs in `_enrichment` (auto-populated from APIs), not in the hand-curated `topics` field.
- Define your vocabulary in a hub note (e.g., `notes/hubs/vocabulary.md`) and review it annually.
- When renaming a topic term, use Obsidian tag-wrangler or a Linter `schema-migrate` dry-run — never search-replace across notes manually.

---

## Slug conventions for wikilinks

| Note type | Slug format | Example |
| --- | --- | --- |
| `paper` | Citekey (Better BibTeX format) | `mamykina2010sense` |
| `claim` | Lowercase kebab-case, subject-verb-object | `receptivity-decreases-under-high-cognitive-load` |
| `hub` | `<topic>-hub` | `jitai-design-hub` |
| `person` | `<lastname>-<firstname>` | `mamykina-lena` |
| `organization` | Slug of the official name | `columbia-dbmi` |
| `venue` | Slug of the venue name | `chi-conference` |
| All others | Descriptive kebab-case | `ema-best-practices` |

Slugs are permanent — renaming a note breaks all wikilinks pointing to the old slug. Rename sparingly and run the Linter's `graph-analyze` check after any rename.

---

## Related

- How-to for setting authored links: [Link related claims](../how-to-guides/compile/link-related-claims.md)
- Why the Connections section is load-bearing: [Note body structure](../explanation/knowledge/note-body-structure.md)
- Why notes are filed by lifecycle, not topic: [Lifecycle, not topic — and state, not folders](../explanation/knowledge/lifecycle-over-topic.md)
- How links keep the vault compounding: [The knowledge cycle](../explanation/knowledge/knowledge-cycle.md)
