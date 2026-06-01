# Linking

Wikilink conventions, typed-relation vocabulary, cross-link topology, and MOC creation thresholds. For the conceptual model see [explanation/vault/](../explanation/architecture/vault.md).

---

## Link types

| Type | Syntax | Direction | Use |
| --- | --- | --- | --- |
| `citekey-link` | `[[mamykina2010sense]]` | `claim-note` → `paper-note` | Link a claim to its supporting paper. |
| `concept-link` | `[[receptivity-decreases-under-high-cognitive-load]]` | `claim-note` ↔ `claim-note` | Connect related claims; builds the knowledge graph. |
| `moc-link` | `[[jitai-design-moc]]` | Note → `moc` | Place a note within a navigational hub. |
| `entity-link` | `[[mamykina-lena]]` | Any → entity or `item-note` | Connect people, organizations, venues, tools. |
| `agent-cross-link` | Inline in note body | Proposed | Agent-generated candidates; human confirms before treating as canonical. |

---

## Linking rules

- Link for usefulness, not completeness.
- Every `claim-note` must trace to at least one `paper-note` citekey.
- Every `paper-note` should eventually connect to at least one relevant `moc`.
- Use concept links only when the relationship would matter in a later reading or writing session.
- Prefer one strong MOC link over many weak generic links.
- Provenance direction: claims point to evidence; do not link the other way.
- Never treat an agent-proposed cross-link as canonical until reviewed.
- An orphan note must receive a MOC link or relevant concept links before it is considered complete.
- Do not link a `paper-note` to a `claim-note` as if they were peers; the claim stands on its own and the paper note is its support.

---

## Required patterns by type

| Note type | Required link structure |
| --- | --- |
| `paper-note` | `Cites` and `Cited by` sections (agent-proposed, reviewed at classification). |
| `claim-note` | `sources:` frontmatter listing the note(s) the claim draws on (`[[paper-note]]`, `[[item-note]]`). `Connections` section for conceptual neighbors. |
| `moc` | `moc:` frontmatter links. Body: overview, curated entries, gaps. |
| `reference-note` | Links outward to the core paper notes and claim notes that define the concept or method. |

---

## Typed relations (`relations:` block)

Opt-in on `claim-note` only (ADR-8). Human-set; agent never writes to this block.

```yaml
relations:
  supports:
    - "[[another-claim-note]]"
  contradicts:
    - "[[a-conflicting-claim-note]]"
```

Allowed relation types:

| Relation | Direction |
| --- | --- |
| `supports` | This claim supports the linked claim. |
| `contradicts` | This claim contradicts the linked claim. |

No other relation types are currently defined. Adding a new type requires updating this reference and the Linter's schema-check detector.

---

## Cross-link topology

Expected link graph by note type:

```text
paper-note ({citekey})
  ↔ person-note           (author)
  ↔ venue-note            (published in)
  ↔ organization-note     (author affiliation)
  ↔ item-note             (uses or evaluates)
  ↔ paper-note (other)    (cites / cited by)

claim-note
  → paper-note            (citekey in sources:)
  ↔ claim-note (other)    (concept link — supports / contradicts / refines)
  → moc                   (moc: frontmatter)

person-note
  ↔ paper-note            (authored)
  ↔ organization-note     (affiliated with)

organization-note
  ↔ person-note           (members, affiliates)
  ↔ venue-note            (hosts or sponsors)

venue-note
  ↔ paper-note            (published)

moc
  ← claim-note            (moc: frontmatter on claims)
  ← paper-note            (moc: frontmatter on papers)
  ↔ moc (other)           (parent/child MOC hierarchy)

reference-note
  → claim-note            (synthesized from)
  → paper-note            (evidence base)

project-note
  ← workbench artifacts   (40-workbench/<project>/* all reference the project note)
```

---

## MOC thresholds

| Threshold | Action |
| --- | --- |
| ≥ 15–20 notes (papers + claims combined) on a topic | Create a top-level MOC for the topic. |
| > 20 claim notes + > 10 paper notes on a branch | Build a child MOC for that branch. |

Do not create a MOC before these thresholds. Below the threshold, live with the lack of a hub — the friction is lower than the cost of maintaining a premature MOC.

---

## Vocabulary discipline

The `topic`, `study_design`, and `methods` fields are open — Memoria does not enforce a controlled vocabulary. Guidelines:

- Keep the active `topic` list to **~30 terms** per corpus. A smaller vocabulary produces more consistent classification.
- Richer taxonomy (MeSH, ACM CCS, OpenAlex concepts) belongs in `_enrichment` (auto-populated from APIs), not in the hand-curated `topic` field.
- Define your vocabulary in a reference note (e.g., `00-meta/04-reference/vocabulary.md`) and review it annually.
- When renaming a topic term, use Obsidian tag-wrangler or a Linter `schema-migrate` dry-run — never search-replace across notes manually.

---

## Slug conventions for wikilinks

| Note type | Slug format | Example |
| --- | --- | --- |
| `paper-note` | Citekey (Better BibTeX format) | `mamykina2010sense` |
| `claim-note` | Lowercase kebab-case, subject-verb-object | `receptivity-decreases-under-high-cognitive-load` |
| `moc` | `<topic>-moc` | `jitai-design-moc` |
| `person-note` | `<lastname>-<firstname>` | `mamykina-lena` |
| `organization-note` | Slug of the official name | `columbia-dbmi` |
| `venue-note` | Slug of the venue name | `chi-conference` |
| All others | Descriptive kebab-case | `ema-best-practices` |

Slugs are permanent — renaming a note breaks all wikilinks pointing to the old slug. Rename sparingly and run the Linter's `graph-analyze` check after any rename.
