---
title: How to promote a claim to canonical reference
parent: Sources
---


# How to promote a claim to canonical reference

Move an evergreen claim note from `30-synthesis/01-claims/` to `30-synthesis/02-reference/` once it has enough cross-links to be treated as settled knowledge.

## Prerequisites

- The claim note is at `maturity: evergreen` (cross-linked from at least 3 distinct sources or claim notes)
- The note does **not** carry `superseded_by` — superseded claims do not promote

## Steps

**1. Find promotion candidates in the weekly review.**

The `weekly-review.md` dashboard's "Promotion queue" section surfaces all claim notes at `maturity: evergreen` that haven't been promoted yet. Open the note from there.

**2. Write a framing introduction** (optional but recommended for important claims).

A reference note may be read months from now without the original context. Add 1–2 sentences at the top framing what this claim asserts and why it matters. This is the note's "canonical version" — write it for that reader.

**3. Move the file to `30-synthesis/02-reference/`.**

In Obsidian: right-click the note → Move file → `30-synthesis/02-reference/`. You may rename the file to a cleaner reference title if the current name is too narrow (e.g., `receptivity-decreases-under-high-cognitive-load.md` → `cognitive-load-and-receptivity.md`).

If you rename, update any `[[wikilinks]]` to this note elsewhere in the vault. Obsidian can do this automatically: right-click → Rename → confirm "Update links."

**4. Set `lifecycle: current` and `promoted_date` in frontmatter.**

```yaml
lifecycle: current
promoted_date: 2026-05-31
```

(`current` is the canonical, human-reviewed state — there is no `canonical` lifecycle value; see [frontmatter.md](../../reference/frontmatter.md#lifecycle-values).)

**5. Add a MOC entry** (if a relevant MOC exists).

Open the Map of Contents note for this topic (e.g., `[[jitai-design-moc]]`) and add a link to the newly promoted note under the appropriate heading.

If no MOC exists yet and this is the third or fourth note on this topic, consider creating one.

## Verify

- The note is in `30-synthesis/02-reference/` with `lifecycle: current`
- The "Promotion queue" on `weekly-review.md` no longer lists this note
- All existing `[[wikilinks]]` to this note still resolve (check Obsidian's backlinks panel)

## Notes

**Do not promote a note just to clear the queue.** The promotion decision is a judgment that this claim represents settled knowledge in your corpus. If you're uncertain, leave it at `maturity: evergreen` in `01-claims/` — that is not a penalty state.

**Superseded claims stay in `01-claims/`.** A claim with `superseded_by` set is intentionally excluded from the promotion queue — it represents prior belief, not current knowledge.

## Related

- Previous step: [Write a claim note](write-a-claim-note.md) (maturity accumulates there)
- Weekly review (step 5 — promote evergreen claims): [run-the-weekly-review.md](../maintenance/run-the-weekly-review.md)
- Add the MOC entry (step 5): [build-a-moc.md](../maintenance/build-a-moc.md)
- MOC creation thresholds: [linking.md](../../reference/linking.md#moc-thresholds)
- The rules promotion enforces: [promotion-model.md](../../explanation/knowledge/promotion-model.md)
