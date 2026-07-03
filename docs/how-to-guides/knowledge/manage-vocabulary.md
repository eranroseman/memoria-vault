---
title: Manage your topic vocabulary
parent: Knowledge
grand_parent: How-to guides
nav_order: 6
---

# Manage your topic vocabulary

Keep the `research_area`, `methodology`, and `topics` values consistent across your corpus — so Dataview and Bases views stay reliable and classification stays navigable as the vault grows. The controlled lists live in **`system/vocabulary.md`**, which ships with the vault (and is golden-copied, so the Linter can detect drift from the shipped scaffold once you've made it yours).

These vocabularies are deliberately **open** — yours to define. The fixed Memoria vocabularies (lifecycle, maturity, certainty, card types) are schema-enforced and not yours to extend.

## When to do each task

| Trigger | Task |
| --- | --- |
| Starting a new corpus | Define your initial lists |
| The active list exceeds ~30 terms | Prune and consolidate |
| A term's meaning has drifted or split | Rename it safely |
| Annually, or after a major reading batch | Full vocabulary review |

## Step 1 — Make `system/vocabulary.md` yours

Open it and structure one section per field:

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

Keep each list to **~30 terms**. A tighter vocabulary produces more consistent classification and more reliable queries ([Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)).

Note the consumers: the ingest operation's automated classify stage rolls OpenAlex topics into `research_area` on paper entities ([Ingest routing](../../reference/ingest.md)); you carry the same terms onto source notes and use `topics` on claims. Your list is what keeps the human side consistent with the automated side.

## Step 2 — Add a new term

1. Check the relevant section first — the term may already exist under another name. That check is the whole discipline.
2. Add it to `system/vocabulary.md`, then use it in the note you're classifying.
3. If the list is already at ~30, ask whether an existing term covers the ground before adding.

`memoria project gaps` can surface repeated off-vocabulary Work phrases as Inbox tag candidates; review those cards, then add only the terms you want to keep.

## Step 3 — Rename a term safely

Renaming a vocabulary value across a fresh alpha.11 sandbox is a
git-disciplined manual pass: commit, enumerate, edit, lint, and commit. The two
vocabulary-specific points:

- **Also update `system/vocabulary.md`** in the same pass — the controlled list and the notes must move together.
- **Your selector is a frontmatter value**, so enumerate with Obsidian global search for the old term (or `grep -rl "old-term" notes/ catalog/`) before editing.

## Step 4 — Annual vocabulary review

Once a year (or after a major reading batch), walk each list:

1. **Prune** terms appearing on fewer than ~3 notes — they're not load-bearing.
2. **Consolidate** terms that drifted to mean the same thing (rename the smaller into the larger, per Step 3).
3. **Split** a term that now covers two distinct concepts.

## Verify

- `system/vocabulary.md` reflects the current active lists, each ≤ ~30 terms
- A grep for each removed term returns no frontmatter hits
- The Linter's `schema-check` and `dashboard-field-drift` detectors report nothing new

## Related

- Where the automated side applies terms: [Classify a source](../library/classify-a-source.md)
- The validation pass: [Run the Linter](../operate/run-the-linter.md)
- Why three open fields and a small list: [Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)
