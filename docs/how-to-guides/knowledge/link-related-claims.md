---
title: Link checked notes
parent: Knowledge
grand_parent: How-to guides
nav_order: 2
---

# Link checked notes

Add a typed `supports` / `contradicts` / `extends` link between checked
`note` Concepts. The PI chooses whether a relationship is real; the worker only
records and traces the accepted edit.

> **`links:` vs `relationships`.** `links:` are authored edges on notes (your thinking); `relationships` are given edges on Catalog entities (facts from the record, written by the ingest operation) ([ADR-52](../../adr/52-links-vs-relationships.md)).

## Prerequisites

- At least two checked notes under `knowledge/notes/`
- The target relationship is your judgment, not an automatic promotion

## Steps

**1. Decide whether the relationship is worth typing.**

Link for usefulness, not completeness. Add a typed link only when "*what contradicts X?*" or "*what supports X?*" would matter in a later reading or writing session. Untyped concept links (a plain `[[wikilink]]` in the body) remain first-class — don't promote every connection.

**2. Pick the link type.**

| Link | Meaning | Direction |
| --- | --- | --- |
| `supports` | This note supports the linked note | Directional — set it on the supporting note |
| `contradicts` | The two notes disagree | Symmetric — set it on either; the graph reads both ways |
| `extends` | This note elaborates the linked note | Directional — set it on the elaborating note |

**3. Queue the link through the Inspector or edit directly.**

In the Inspector control panel, set the source note path, target path, and link
type, then enqueue the matching link action. The worker records the journal row
and commits the checked note update.

For a direct PI edit, extend the note's `links:` map:

```yaml
links:
  supports: []
  contradicts:
    - knowledge/notes/receptivity-decreases-under-high-cognitive-load.md
```

Both keys can carry lists — a claim may support one claim and contradict another.

**4. Point with the exact note name.**

The target is the vault-relative path to the other checked note. Copy it from
the target file rather than retyping.

**5. Let agents propose; confirm yourself.**

The worker and plugin can surface candidate connections, but never copy a
proposed link unread. The agent proposes; you dispose.

**6. Confirm it surfaced.**

Run the project argument analysis or render the project argument Canvas. The
typed edge should appear with its label.

## Verify

- The `links:` keys stay within `supports` / `contradicts` / `extends`
- Project argument analysis sees the edge
- Every link target resolves to a checked note

## Related

- Analyze the resulting graph: [Analyze a project argument](../project/analyze-a-project-argument.md)
- The two edge kinds: [Frontmatter fields](../../reference/frontmatter.md)
- Why connections are load-bearing: [Note body structure](../../explanation/knowledge/note-body-structure.md)
