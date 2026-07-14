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
vault. The schema/linter checks note `topics` membership; it does not validate
the vocabulary file or catalog Work classifications.

Use this guide when you need to add one useful term or rename one that has
drifted.

## Steps

Vocabulary mutations are PI-only. Use the local CLI so each mutation is
journaled and committed; do not expose that CLI to an untrusted agent.

**1. Inspect the current lists.**

```bash
memoria vocab list --workspace <workspace>
```

The command reads `system/vocabulary.md`. The mutable lists are
`research_area` and `methodology`; note `topics` inherit the `research_area`
list:

```markdown
## research_area
- receptivity-detection — Claims and Works about receptivity.
- ema-experience-sampling — Claims and Works about in-situ sampling.

## methodology
- field-study — In-situ deployment study.
- qualitative-interview — Interview-led qualitative inquiry.

## topics
Claim-bearing note topics draw from research_area above.
```

Keep `research_area` to roughly 30 terms. Prefer renaming or merging before
adding a near-duplicate to either mutable list.

**2. Add a new term only after checking the list.**

1. Check the relevant section first — the term may already exist under another name. That check is the whole discipline.
2. Add it through the PI-owned command, then use it in the note you're classifying:

   ```bash
   memoria vocab add --workspace <workspace> research_area care-access-barriers
   ```

3. If the list is already at ~30, ask whether an existing term covers the ground before adding.

**3. Rename a term safely.**

Rename the controlled-list value through the PI-owned command:

```bash
memoria vocab rename --workspace <workspace> research_area old-term new-term
```

Then enumerate and update existing uses. The command changes and records the
controlled list; it does not rewrite Concepts or catalog rows. The two
vocabulary-specific points are:

- **Update every existing use in the same pass.** Edit Concept frontmatter as
  the PI and run `memoria workspace scan --workspace <workspace>`; use
  `memoria work update --research-area` or `--methodology` for catalog Work
  changes.
- **Your selector is a frontmatter or catalog metadata value**, so enumerate with
  `memoria ask`/read-API inspection, Obsidian global search, or `grep -rl
  "old-term" digests/ fulltexts/ notes/ hubs/ projects/ system/` before editing
  Concepts. Use `memoria work export` for catalog Work metadata.

**4. Prune as you rename.**

When a term appears on only a few notes, decide whether it is really
load-bearing. Merge it into a broader term if queries do not need the narrower
distinction. Record the list merge with:

```bash
memoria vocab merge --workspace <workspace> research_area narrow-term broader-term
```

As with rename, update existing Work `research_area` and note `topics` uses
separately. Mutating `topics` directly is rejected because it has no independent
controlled list.

Update an existing Work classification with the matching repeatable flag:

```bash
memoria work update --workspace <workspace> <work-id> \
  --research-area personal-informatics \
  --methodology field-study
```

Work has no `topics` field. Claim-bearing note `topics` continue to draw from
the `research_area` controlled list.

## Verify

- `system/vocabulary.md` reflects the current active lists, with
  `research_area` roughly 30 terms or fewer
- A grep for each removed term returns no frontmatter hits
- The Linter's `schema-check` detector reports no off-vocabulary note `topics`

## Related

- The validation pass: [Run the Linter](../operate/run-the-linter.md)
- Why three open fields and a small list: [Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)
