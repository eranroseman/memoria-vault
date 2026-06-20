---
title: Refactor claim notes
parent: Knowledge
grand_parent: How-to guides
nav_order: 5
---

# Refactor claim notes

Keep claim notes atomic and remove duplication without losing provenance. Agents surface the candidates; every structural decision — merge, split, or leave — is yours, because `notes/claims/` is review-gated.

## When to refactor

- A claim's body contains an "and" doing real work — two distinct ideas in one note
- A duplicate hunt flags two notes saying the same thing in different words
- A note has grown to where you hesitate to link it because only part of it applies

## Find duplicate candidates

Delegate the hunt from the Co-PI pane:

> "Verify my claims on `<topic>` for near-duplicates."

The Peer-reviewer's `verify` lane (and the sweeps operation's similarity checks) return findings as **flag cards** in the Inbox, each naming the suspect pair. Nothing is auto-merged — the lane can only write cards.

## Merge two notes into one

1. **Review the pair side by side.** Decide which is the stronger formulation.
2. **Combine the content.** Copy any non-redundant Evidence from the weaker note into the stronger.
3. **Merge the sources.** Union the citekeys into the stronger note's `sources:`.
4. **Merge the links.** Carry any `supports` / `contradicts` entries (and `topics`) the weaker note held.
5. **Redirect backlinks.** Search for wikilinks to the weaker note and point them at the stronger one; update any hub `members` lists.
6. **Archive the weaker note.** Set `lifecycle: archived` and `superseded_by: "[[stronger-note]]"`. Do not delete — the note has provenance value, and the Linter's `fama-exposure` detector will flag anything still leaning on it.

## Split one note into two

1. **Create the second note** via `Cmd/Ctrl-P` → **Memoria: write claim note**.
2. **Move the second claim** out of the original's body — each note one falsifiable sentence.
3. **Divide the sources.** Assign citekeys to whichever claim each source actually supports.
4. **Link the pair** if they relate: a `supports` or `contradicts` entry in `links:`.
5. **Update backlinks and hub members** to point at the right half.

## Verify

- Each resulting note states exactly one claim, with every Evidence line tracing to its own `sources`
- The archived note carries `superseded_by`, and no active note wikilinks it (the `fama-exposure` detector confirms on its next pass)
- The flag card that started this is resolved

## Related

- Validation after structural edits: [Run the Linter](../operate/run-the-linter.md)
- The compound-note failure this fixes: [Common pitfalls](../../explanation/knowledge/common-pitfalls.md)
- The note shape you're refactoring toward: [Note body structure](../../explanation/knowledge/note-body-structure.md)
- The lane that surfaces candidates: [The Peer-reviewer](../../explanation/profiles/peer-reviewer.md)
