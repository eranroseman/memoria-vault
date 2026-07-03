---
title: Archive a source
parent: Library
grand_parent: How-to guides
nav_order: 8
---

# Archive a source

Retire a Work that is no longer active: superseded, irrelevant to current
projects, or fully processed with nothing new to extract. Archiving is a
catalog standing change, not a folder move.

## Prerequisites

- The Work is checked/current, or you've decided it should not be processed further

## Steps

**1. Confirm there is no open work for this source.**

Check request and attention state for the Work ID or citekey:

```bash
memoria request list --workspace <workspace>
memoria attention list --workspace <workspace>
```

Cancel obsolete requests or resolve obsolete attention before archiving:

```bash
memoria request cancel --workspace <workspace> <request-id>
memoria attention resolve --workspace <workspace> <attention-path> --reject
```

**2. Archive the Work row.**

Use the CLI so the worker records the change through the request lifecycle:

```bash
memoria work update --workspace <workspace> <work-id> --standing archived
```

Use `--standing superseded` or `--standing retracted` instead when that is the
real reason.

**3. Recheck claims that cite this Work.**

Archive does not delete evidence. If the archive was prompted by a retraction,
run the retraction sweep and revisit claims deliberately: soften, supersede, or
caveat.

## Verify

- The `memoria work update --json` result or request record reports `standing: archived`
- No open request or attention item references this Work
- Checked notes citing this Work still resolve their evidence

## When not to archive

Do not archive a Work just to clear it from a queue. If a source has sat unread
but you still plan to read it, leave it current and let the queue show the
backpressure. Archive only when you've made a deliberate decision that this Work
is done.

## Related

- Weekly review (surfaces stale sources): [Run the weekly review](../inbox/run-the-weekly-review.md)
- Lifecycle field values: [Frontmatter fields](../../reference/frontmatter.md)
- Why archived notes aren't deleted: [The knowledge cycle](../../explanation/knowledge/knowledge-cycle.md)
- What happens on a retraction hit: [Run a retraction sweep](../operate/run-a-retraction-sweep.md)
