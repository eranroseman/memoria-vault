---
title: Archive a source
parent: Library
grand_parent: How-to guides
nav_order: 8
---

# Archive a source

Retire a source note that is no longer active — superseded, irrelevant to current projects, or fully processed with nothing new to extract. Archiving is a **lifecycle change, not a folder move**: the note stays where it is and `lifecycle: archived` takes it out of every active view.

## Prerequisites

- The source note is at `lifecycle: current` (fully distilled), or you've decided it won't be processed further

## Steps

**1. Confirm there are no open board cards for this source.**

Check for open cards referencing this citekey ([Hermes CLI](../../reference/hermes-cli.md#board-management)):

```bash
hermes kanban list
```

If an open card references the citekey, archive it with a reason first:

```bash
hermes kanban archive <card-id> --reason "source archived: superseded"
```

**2. Open the source Concept in Obsidian.**

Use the Library space's source views or Obsidian search to open the source
Concept. The on-disk path is `catalog/sources/<source_id>/source.md`, but
navigation should start from the space/Bases surface.

**3. Set `lifecycle: archived` in frontmatter.**

```yaml
lifecycle: archived
```

Add one line at the top of the body saying why ("superseded by newer work", "out of scope", "fully processed"). This is the only record of why this source left the active pool.

**4. Decide whether the Catalog entity archives too.**

The source Concept at `catalog/sources/<source_id>/source.md` is the bibliographic
record, not your reading of it. Set `lifecycle: archived` only when the record
itself should leave active Catalog views. For a retracted source, use
`lifecycle: retracted`.

**5. Confirm any claims that cite this source still stand.**

Open the backlinks panel before walking away. Claims citing the source remain valid — the source is archived, not deleted, and every `sources:` citekey still resolves. If the archive was prompted by a retraction, revisit those claims deliberately (soften, supersede, or caveat).

## Verify

- The source Concept carries `lifecycle: archived` and no longer appears in active Catalog views
- No open board cards reference this citekey
- Checked notes citing this source still resolve their `evidence_set`

## When not to archive

Do not archive a source just to clear it from a queue. If a source has sat unread for weeks but you still plan to read it, leave it at `lifecycle: proposed` — the backpressure is intentional. Archive only when you've made a deliberate decision that this source is done.

## Related

- Weekly review (surfaces stale sources): [Run the weekly review](../inbox/run-the-weekly-review.md)
- Lifecycle field values: [Frontmatter fields](../../reference/frontmatter.md)
- Why archived notes aren't deleted: [The knowledge cycle](../../explanation/knowledge/knowledge-cycle.md)
- What happens on a retraction hit: [Run a retraction sweep](../operate/run-a-retraction-sweep.md)
