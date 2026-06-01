# How to refactor claim notes

This guide shows you how to keep claim notes atomic and remove duplication without losing provenance.

## When to refactor

- A claim note's body contains "and" doing real work — two distinct ideas in one note
- The Verifier's `find-duplicates` flags two notes with high similarity (≥ 0.85)
- A note has grown to the point where you hesitate to link to it because only part of it applies

## Find duplicate candidates

The Verifier identifies near-duplicate notes using embedding similarity:

```bash
hermes -p memoria-verifier chat -s find-duplicates
```

Then in the session:

```text
/find-duplicates --folder 30-synthesis/01-claims --threshold 0.85
```

The Verifier returns pairs with similarity scores. It never auto-merges.

## Merge two notes into one

1. **Review the pair.** Open both notes side by side. Decide which is the stronger formulation.
2. **Combine the content.** Copy any non-redundant body text from the weaker note into the stronger.
3. **Merge the sources.** Add all citekeys from the weaker note's `sources:` to the stronger note's `sources:`.
4. **Update backlinks.** Search for wikilinks pointing to the weaker note (`[[weaker-note-title]]`) and redirect them to the stronger note.
5. **Update MOC entries.** If the weaker note was in any MOC's member list, replace it with the stronger note.
6. **Archive the weaker note.** Set `lifecycle: archived` and add `superseded_by: [[stronger-note-title]]`. Do not delete — the note has provenance value.

## Split one note into two

1. **Create the second note** using `Cmd+P → Memoria: write claim note`.
2. **Move the second claim** from the original note's body into the new note.
3. **Divide the sources.** Assign source citekeys to whichever note each source actually supports.
4. **Link the pair** if they're related: add a `relations: supports` or `relations: contradicts` entry as appropriate.
5. **Update MOC entries** and backlinks to point to the correct note.

## Owners

The Verifier surfaces candidates. You make every structural decision — merge, split, or leave.

---

## Related

- The compound-note failure refactoring fixes: [common-pitfalls.md](../../explanation/knowledge/common-pitfalls.md)
- The note structure you are refactoring toward: [note-body-structure.md](../../explanation/knowledge/note-body-structure.md)
- Note types and their boundaries: [note-types.md](../../explanation/knowledge/note-types.md)
- Run the Linter after structural edits: [run-the-linter.md](run-the-linter.md)
