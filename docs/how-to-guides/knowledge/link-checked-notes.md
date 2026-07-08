---
title: Link checked notes
parent: Knowledge
grand_parent: How-to guides
nav_order: 2
---

# Link checked notes

Add a typed link between two checked notes when the relationship will help later
reading, querying, or drafting.

## Prerequisites

- At least two checked notes under `notes/`
- The target relationship is your judgment, not an automatic promotion

## Steps

**1. Decide whether the relationship is worth typing.**

Link for usefulness, not completeness. Add a typed link only when "*what contradicts X?*" or "*what supports X?*" would matter in a later reading or writing session. Untyped concept links (a plain `[[wikilink]]` in the body) remain first-class — don't promote every connection.

**2. Pick the link type.**

Use `supports` when one note strengthens another, `contradicts` when the notes
disagree, and `extends` when one note elaborates another.

**3. Record the link through the CLI or edit directly.**

Run the link command with the starting note path, link type, and target path. The
worker records the journal row and commits the checked note update.

```bash
memoria link --workspace <vault> notes/receptivity-varies-by-burden.md \
  notes/receptivity-decreases-under-high-cognitive-load.md --rel contradicts
```

For a direct PI edit, extend the note's `links:` map:

```yaml
links:
  supports: []
  contradicts:
    - notes/receptivity-decreases-under-high-cognitive-load.md
```

Both keys can carry lists — a claim may support one claim and contradict another.

**4. Point with the exact note name.**

The target is the vault-relative path to the other checked note. Copy it from
the target file rather than retyping.

**5. Let agents propose; confirm yourself.**

The worker and optional adapters can surface candidate connections, but never copy a
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
- Exact link fields: [Frontmatter fields](../../reference/frontmatter.md)
- Why connections are load-bearing: [Note body structure](../../explanation/knowledge/note-body-structure.md)
