---
topic: vault
---

# Linking patterns

The authoritative reference for vault linking discipline: link types, the full rule set, the expected cross-link graph by note type, MOC creation thresholds, and slug-collision resolution. The summary lives in [vault/README.md](../explanation/vault/README.md#linking-patterns); this document is the full reference.

## Link types

| Type | Syntax | Use | Direction |
| --- | --- | --- | --- |
| `citekey-link` | `[[mamykina2010sense]]` | Link a claim to its paper note. | `claim-note` → `paper-note` |
| `concept-link` | `[[receptivity-decreases-under-high-cognitive-load]]` | Link related claims and build the knowledge graph. | `claim-note` ↔ `claim-note` |
| `moc-link` | `[[jitai-design-moc]]` | Place a note within a navigational hub. | Note → `moc` |
| `entity-link` | `[[mamykina-lena]]` | Connect people, organizations, venues, tools. | Any → `entity-*` / `item-note` |
| `agent-cross-link` | Generated in note body | Surface citation-graph and related-note candidates. | Proposed by agent, confirmed by human. |

## Linking rules

- Link for usefulness, not completeness.
- Every `claim-note` should trace to at least one `paper-note` citekey.
- Every `paper-note` should eventually connect to at least one relevant `moc`.
- Use concept links only when the relationship would matter in a later reading or writing session.
- Prefer one strong MOC link over many weak generic links.
- Preserve provenance direction: claims point to evidence, not the other way around.
- Never treat agent-generated cross-links as canonical until they have been reviewed.
- If a note becomes an orphan, add a MOC link or relevant concept links before considering it complete.
- Do not link a `paper-note` to a `claim-note` as if they were peers; the claim should stand on its own with the paper note as support.

## Required patterns

- **Paper notes** — include `Cites` and `Cited by` sections when relevant, with agent-proposed links reviewed during classification.
- **Claim notes** — include source links in body text and keep a `Connections` section for meaningful conceptual neighbors.
- **MOCs** — use frontmatter `moc:` links and keep the MOC body focused on overview, curated entries, and gaps.
- **Reference notes** — link outward to the core paper notes and claim notes that define the concept, method, or domain.

## Cross-link graph

The expected link topology — what links to what — by note type:

```text
paper-note ({citekey})
  ↔ person-note         (author)
  ↔ venue-note          (published in)
  ↔ organization-note   (author affiliation)
  ↔ item-note           (uses or evaluates)
  ↔ paper-note (other)  (cites / cited by)

claim-note
  → paper-note          (citekey, supports the claim)
  ↔ claim-note (other)  (concept link — supports, contradicts, refines)
  → moc                 (frontmatter moc:)

person-note
  ↔ paper-note          (authored)
  ↔ organization-note   (affiliated with)

organization-note
  ↔ person-note         (members, affiliates)
  ↔ paper-note          (institutional output)

item-note
  ↔ paper-note          (cited in or evaluating)
  ↔ organization-note   (maintained by)
  ↔ code-note           (used in project)

code-note
  → paper-note          (motivating evidence)
  → project-note        (project it belongs to)
  → item-note           (dependencies)
```

Single arrows (`→`) indicate a one-directional link; the note on the left (the source) carries the pointer. Double arrows (`↔`) are bidirectional — both notes carry pointers.

**Co-authorship is not a direct link.** Two `person-note`s linked because they co-authored a paper would duplicate the paper note's author list and force every paper to spawn new edges. Instead, co-authorship is expressed *indirectly* through shared `paper-note` authorship: querying "papers by A" ∩ "papers by B" surfaces the relationship without a maintained edge. Advisor/advisee or other persistent relationships *are* direct edges — they outlast any single paper.

## MOC creation thresholds

MOCs require enough mass to be worth navigating. Building them too early creates maintenance burden for no payoff.

| Threshold | Rule |
| --- | --- |
| **Do not create at init** | A new vault should not have MOCs. Dataview queries and search cover navigation until clusters form. |
| **Topic MOC** | Create when a topic has **≥ 15–20 notes** between `20-sources/01-papers/` and `30-synthesis/01-claims/`. |
| **Domain MOC** | Create when there are **at least 3 topic MOCs** that share a domain. A domain MOC with one child topic is just a topic MOC with extra steps. |
| **Child MOC** | Split a parent when a branch has **> 20 claim notes and > 10 paper notes**. |
| **Project MOC** | One per dissertation chapter or formal review. Create on project start; archive on project close. |

These thresholds prevent MOC sprawl (too many empty hubs) and MOC underuse (one giant MOC that should be three).

## Slug collision resolution

The naming conventions are designed so collisions are rare. When they do occur:

| Collision | Resolution pattern |
| --- | --- |
| Two researchers with same name | Append disambiguator: `smith-john-iowa.md` vs `smith-john-stanford.md` |
| Two labs with similar names | Use full institution: `hci-lab-iowa.md` vs `hci-lab-cmu.md` |
| Person and organization share surname | Person keeps bare slug; org gets `-org` suffix: `mamykina.md` vs `mamykina-org.md` |
| Same package on different registries | Registry prefix: `pypi-requests.md` vs `npm-requests.md` |
| Repo and person collide | Repos always have `{owner}-` prefix; no collision possible by construction |

When a new note triggers a collision, the Linter flags it for human disambiguation — never silently merges or renames.
