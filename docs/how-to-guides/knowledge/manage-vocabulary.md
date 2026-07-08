---
title: Manage vocabulary
parent: Knowledge
grand_parent: How-to guides
nav_order: 4
---

# Manage vocabulary

Keep the `research_area`, `methodology`, and `topics` values consistent across
your corpus so CLI/read-API queries and optional editor views stay reliable.
The controlled lists live in **`system/vocabulary.md`**, which ships with the
vault and is checked by the schema/linter surfaces once you've made it yours.

Use this guide when you need to add one useful term or rename one that has
drifted.

## Steps

**1. Open `system/vocabulary.md`.**

Keep one section per field:

```markdown
## research_area
- receptivity-detection
- ema-experience-sampling
- health-equity

## methodology
- field-study
- qualitative-interview
- meta-analysis

## topics (claims)
- receptivity-timing
- sensemaking
```

Keep each list to roughly 30 terms. If a section is already long, prefer
renaming or merging before adding another near-duplicate.

**2. Add a new term only after checking the list.**

1. Check the relevant section first — the term may already exist under another name. That check is the whole discipline.
2. Add it to `system/vocabulary.md`, then use it in the note you're classifying.
3. If the list is already at ~30, ask whether an existing term covers the ground before adding.

**3. Rename a term safely.**

Renaming a vocabulary value across a fresh standalone workspace is a
git-disciplined manual pass: commit, enumerate, edit, lint, and commit. The two
vocabulary-specific points:

- **Also update `system/vocabulary.md`** in the same pass — the controlled list and the notes must move together.
- **Your selector is a frontmatter or catalog metadata value**, so enumerate with
  `memoria ask`/read-API inspection, Obsidian global search, or `grep -rl
  "old-term" digests/ fulltexts/ notes/ hubs/ projects/ system/` before editing
  Concepts. Use `memoria work export` for catalog Work metadata.

**4. Prune as you rename.**

When a term appears on only a few notes, decide whether it is really
load-bearing. Merge it into a broader term if queries do not need the narrower
distinction.

## Verify

- `system/vocabulary.md` reflects the current active lists, each roughly 30 terms or fewer
- A grep for each removed term returns no frontmatter hits
- The Linter's `schema-check` and `dashboard-field-drift` detectors report nothing new

## Related

- The validation pass: [Run the Linter](../operate/run-the-linter.md)
- Why three open fields and a small list: [Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)
