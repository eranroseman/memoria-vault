---
title: Link related claims
parent: Knowledge
grand_parent: How-to guides
nav_order: 2
---

# Link related claims

Add a typed `supports` / `contradicts` link between two claims that **already exist**; to set one while writing a claim, see [Write a claim note](write-a-claim-note.md).

> **`links:` vs `relationships`.** `links:` are authored edges on notes (your thinking); `relationships` are given edges on Catalog entities (facts from the record, written by the ingest operation) ([ADR-52](../../adr/52-links-vs-relationships.md)).

## Prerequisites

- At least two claim notes in `notes/claims/`
- These links are yours to set — `notes/claims/` is review-gated; agents only *propose*, never write

## Steps

**1. Decide whether the relationship is worth typing.**

Link for usefulness, not completeness. Add a typed link only when "*what contradicts X?*" or "*what supports X?*" would matter in a later reading or writing session. Untyped concept links (a plain `[[wikilink]]` in the body) remain first-class — don't promote every connection.

**2. Pick the link type.**

| Link | Meaning | Direction |
| --- | --- | --- |
| `supports` | This claim supports the linked claim | Directional — set it on the supporting claim |
| `contradicts` | The two claims disagree | Symmetric — set it on either; the dashboard reads both ways |

If the relationship is *temporal replacement* — this claim makes an older one obsolete — that is **not** a `links:` entry; it's supersession (`superseded_by` on the old claim), covered in [Advance a claim to evergreen](promote-a-claim.md).

**3. Add the entry to the claim's `links:` map.**

Open the claim note and extend the frontmatter block the claim template ships:

```yaml
links:
  supports: []
  contradicts:
    - "[[receptivity-decreases-under-high-cognitive-load]]"
```

Both keys can carry lists — a claim may support one claim and contradict another.

**4. Point with the exact note name.**

The target is a wikilink to the other claim note (lowercase kebab-case, the claim as a sentence). Copy it from the target's filename rather than retyping — the Linter's `frontmatter-link` detector flags any frontmatter wikilink that resolves to no note, but only on its next pass.

**5. Let agents propose; confirm yourself.**

The Librarian's `link` lane surfaces candidate connections and tensions as Inbox proposals ([Review link suggestions](../inbox/review-link-suggestions.md)). Never copy a proposed link into `links:` unread — the agent proposes, you dispose.

**6. Confirm it surfaced.**

For a `contradicts` link, open the Knowledge space's **Contradictions** view. The pair should appear — that visibility is the payoff of typing the link.

## Verify

- The `links:` keys stay within `supports` / `contradicts` (the Linter's `schema-check` flags anything else)
- A `contradicts` pair appears on the contradictions dashboard
- Every link target resolves to a real claim note

## Related

**How-to**

- Set a link while authoring: [Write a claim note](write-a-claim-note.md)
- Triage agent-proposed links: [Review link suggestions](../inbox/review-link-suggestions.md)
- The temporal complement (replacement, not disagreement): [Advance a claim to evergreen](promote-a-claim.md)

**Reference**

- The two edge kinds: [Frontmatter fields](../../reference/frontmatter.md)

**Explanation**

- The consumer: [The contradictions dashboard](../../explanation/dashboards/synthesis-agenda/contradictions.md)
- Why connections are load-bearing: [Note body structure](../../explanation/knowledge/note-body-structure.md)
