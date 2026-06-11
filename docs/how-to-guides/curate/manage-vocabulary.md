---
title: Manage your topic vocabulary
parent: Curate
nav_order: 4
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

Note the consumers: the ingest engine's automated classify stage rolls OpenAlex topics into `research_area` on paper entities ([Ingest routing](../../reference/ingest.md)); you carry the same terms onto source notes and use `topics` on claims. Your list is what keeps the human side consistent with the automated side.

## Step 2 — Add a new term

1. Check the relevant section first — the term may already exist under another name. That check is the whole discipline.
2. Add it to `system/vocabulary.md`, then use it in the note you're classifying.
3. If the list is already at ~30, ask whether an existing term covers the ground before adding.

## Step 3 — Rename a term safely

There is no automated migration command in v0.1.0-alpha.2 — a rename is a deliberate, git-disciplined pass:

1. **Commit first** so the rename is one reviewable diff: `git add -A && git commit -m "pre-rename snapshot"`.
2. **Find every occurrence:** Obsidian global search for the old term (or `grep -rl "old-term" notes/ catalog/` in the terminal).
3. **Edit each frontmatter occurrence** to the new term. For a large corpus, a scripted `sed` pass over the matched files is fine — you reviewed the file list in step 2.
4. **Update `system/vocabulary.md`.**
5. **Validate:** run the Linter's detectors and review the diff before committing:

```bash
python3 .memoria/engines/linter/detectors.py --vault . 
git diff --stat && git add -A && git commit -m "vocab: rename old-term → new-term"
```

The pre-commit gate re-validates every staged typed note against its schema, so a botched edit blocks the commit instead of landing.

## Step 4 — Annual vocabulary review

Once a year (or after a major reading batch), walk each list:

1. **Prune** terms appearing on fewer than ~3 notes — they're not load-bearing.
2. **Consolidate** terms that drifted to mean the same thing (rename the smaller into the larger, per Step 3).
3. **Split** a term that now covers two distinct concepts.

## Verify

- `system/vocabulary.md` reflects the current active lists, each ≤ ~30 terms
- A grep for each retired term returns no frontmatter hits
- The Linter's `schema-check` and `dashboard-field-drift` detectors report nothing new

## Related

- Where the automated side applies terms: [Classify a source](../compile/classify-a-source.md)
- The validation pass: [Run the Linter](../operate/run-the-linter.md)
- Why three open fields and a small list: [Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)
