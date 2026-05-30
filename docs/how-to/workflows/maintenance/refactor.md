---
topic: workflows
---

# Refactor

**Group.** Maintenance
**Goal.** Keep claim notes atomic and remove duplication without losing provenance.

## Steps

1. The Verifier runs `find-duplicates` to identify duplicate or similar notes.
2. Human reviews candidate pairs.
3. Human merges, splits, or archives.
4. Backlinks and MOCs are updated.

## Owners

The **Verifier** identifies duplicate or near-duplicate notes (via `find-duplicates`). The human decides every change.

## Command

```bash
hermes run find-duplicates --folder 30-synthesis/01-claims --threshold 0.85
```

## Example

`find-duplicates` flags `receptivity-decreases-under-high-cognitive-load.md` and `cognitive-load-lowers-receptivity.md` at 0.88 similarity → the human reviews the pair, decides they're one claim → merges the weaker into the stronger, keeps both source citekeys, and updates backlinks and the `[[jitai-design-moc]]` entry. The merged-away note is archived, not deleted.

## Related

- **Profile:** [profiles/verifier.md](../../../explanation/profiles/verifier.md) (runs `similarity-check` and `find-duplicates`)
- **Pre-filing similarity check** also fires during [Distill](../upstream/distill.md#pre-filing-similarity-check) as a point-of-action duplicate guard.
