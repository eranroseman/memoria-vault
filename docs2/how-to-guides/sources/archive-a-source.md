
# How to archive a source

Retire a source note that is no longer active — superseded, irrelevant to current projects, or fully processed with nothing new to extract.

## Prerequisites

- The note is at `lifecycle: current` (fully processed) or you've decided it won't be processed further

## Steps

**1. Confirm there are no pending cards for this source.**

Check the Kanban board for open `discuss`, `distill`, or `ingest` cards referencing this citekey:

```bash
hermes kanban list --filter citekey=<citekey>
```

If open cards exist, close them with `outcome: archived` before archiving the note.

**2. Open the note in Obsidian.**

Navigate to `20-sources/01-papers/<citekey>.md` or `20-sources/02-items/<citekey>.md`.

**3. Set `lifecycle: archived` in frontmatter.**

```yaml
lifecycle: archived
archived_date: 2026-05-31
archived_reason: "superseded by newer work / out of scope / fully processed"
```

Write a brief reason — this is the only record of why this source left the active pool.

**4. Move the note to `95-archive/`.**

In Obsidian: right-click the note → Move file → `95-archive/`. Keep the same filename.

Alternatively, in the terminal:

```powershell
Move-Item vault\20-sources\01-papers\<citekey>.md vault\95-archive\<citekey>.md
```

**5. Confirm any claim notes that cite this source still stand.**

Open the backlinks panel (Obsidian → Backlinks) before archiving. If claim notes link to this source, they remain valid — the source is archived, not deleted. The `[!brief]` callout and Key Findings in the archived note preserve the rationale.

## Verify

- The note is in `95-archive/` with `lifecycle: archived`
- No open Kanban cards reference this citekey
- Dataview queries that filter on `lifecycle: current` no longer include this note
- Claim notes that cite this source still show their backlinks pointing at `95-archive/<citekey>.md`

## When not to archive

Do not archive a source just to clear it from a queue. If the discuss card has been open for weeks but you still plan to think about the paper, leave it open — the backpressure is intentional. Archive only when you've made a deliberate decision that this source is done.

## Related

- Archive workflow reference: [how-to/workflows/upstream/archive.md](../../memoria-vault/docs/how-to/workflows/upstream/archive.md)
- Lifecycle field values: [reference/frontmatter-schema.md](../../memoria-vault/docs/reference/frontmatter-schema.md)
- Weekly review (surfaces stale sources): [run-the-weekly-review.md](../maintenance/run-the-weekly-review.md)
