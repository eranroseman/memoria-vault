---
title: "Tutorial 04: Build a reading batch"
parent: Tutorials
---


# Tutorial 04: Build a reading batch

**You will end with:** 5 classified paper-notes, 3 linked claim notes, and your first connected knowledge cluster visible in the vault.

**Time:** 2–3 hours (spread across multiple sessions if needed).

**You will use:** Zotero, Obsidian command palette, and the reading-pipeline and open-questions dashboards.

**Prerequisite:** [Tutorial 03](03-bring-in-a-paper.md) complete.

---

## Step 1 — Choose your batch

Add 5 papers to Zotero that are all on the same topic area — the same area as the paper from Tutorial 03.

Choose papers by this criteria:

- Pick papers you've actually been meaning to read, not the most famous ones in the field
- Mix: at least one older foundational paper, two or three recent ones (last 3 years), one you're uncertain about
- Aim for papers that might disagree with each other — divergence produces better claim notes than consensus

After adding all five to Zotero, verify each has a Better BibTeX citekey.

---

## Step 2 — Ingest the batch

For each paper in Zotero, click the item to select it, then:

Press `Cmd+P` → type `capture zotero` → select **Memoria: capture from Zotero selection**.

Do this 5 times, once per paper.

**What you'll see:** Each capture creates an `intake:source` card on the Librarian lane. The Librarian processes them in order. If you open `reading-pipeline.md`, you'll watch the notes arrive one by one over the next few minutes.

Wait until all 5 notes appear in the dashboard before moving on.

---

## Step 3 — Read the briefs

Open each new paper-note. Read its `[!brief]` callout before doing anything else.

By the third or fourth paper, the briefs will reference your earlier papers — "overlaps with `<earlier-citekey>` on receptivity timing." If a brief flags a potential contradiction with an earlier paper, pay extra attention to that section when you read. If it flags a new construct, note it in a fleeting note.

Take brief notes (in a fleeting note, or directly in the paper-note body) about what each paper is actually saying. Not a summary — just the one or two things that matter to your thinking.

---

## Step 4 — Classify all five papers

Work through each paper-note in turn. The classification flow from Tutorial 03:

1. Review `_proposed_classification`
2. Promote the fields you agree with into the main YAML
3. Adjust the terms if needed
4. Delete the `_proposed_classification` block
5. Set `lifecycle: current`

**Pay attention to vocabulary consistency.** If paper 1 uses `topic: receptivity-detection` and the Librarian proposed `topic: opportune-moments` for paper 3 — these probably refer to the same concept. Pick one term and use it across all five. You can always rename later with the Linter's `schema-migrate` command, but consistency now saves work later.

After classifying all five, open `reading-pipeline.md`. All five should show `lifecycle: current`.

---

## Step 5 — Write three claim notes

From the five papers, write three claim notes. Choose claims that:

- You found genuinely surprising, or that changed how you think about the topic
- Appear in more than one paper (multiple sources = stronger grounding)
- Include at least one that *contradicts* or *qualifies* another — the tension is where synthesis happens

For each claim note:

Press `Cmd+P` → type `write claim` → select **Memoria: write claim note**

Fill in:

- **Title:** One falsifiable sentence. Your words, not the paper's.
- **Body:** 3–5 sentences. Why you believe this, what would overturn it, what it connects to.
- **sources:** The citekeys of the papers that support this claim: `[[citekey1]], [[citekey2]]`
- **maturity:** `seedling` (the default — keep it)

If your title contains "and" doing real work, you have two claims — split them into separate notes.

After writing all three, you have a synthesis zone with three permanent notes.

**See also:** [Note types — claim-note](../explanation/knowledge/note-types.md) — atomicity discipline and when to split a compound claim.

---

## Step 6 — Link the claims to each other

Open the first claim note. Read its body. Ask: which of the other two claims does this connect to?

If claim A supports claim B, add to claim A's `relations:` frontmatter:

```yaml
relations:
  supports:
    - "[[claim-b-title]]"
```

If claim A contradicts claim C, add:

```yaml
relations:
  contradicts:
    - "[[claim-c-title]]"
```

Do this for all three claim notes — check whether each connects to the others. Not every note needs to connect to every other; link only where the relationship would matter in a future reading session.

After linking, open the Obsidian graph view (`Cmd+P → Open graph view`). You'll see your 5 paper-notes and 3 claim notes connected.

---

## Step 7 — Check the open-questions dashboard

Open `00-meta/01-dashboards/open-questions.md`.

This dashboard surfaces notes with `lifecycle: proposed` that have been sitting unclassified for too long, and claim notes with no incoming links (orphans). Check it now.

If any of your five papers are still showing as `proposed`, go back and classify them.

If any claim note shows as an orphan (no links in or out), add at least one link — either to a paper-note in `sources:` or to another claim note in `relations:`.

---

## What you have

- 5 classified paper-notes (`lifecycle: current`)
- 3 claim notes (`maturity: seedling`) linked to their source papers
- Some claim-to-claim links in `relations:`
- A visible cluster in the graph view
- `reading-pipeline.md`: 5 items moved through the pipeline
- `open-questions.md`: no orphans

**The `[!brief]` callouts in your earlier papers have also updated.** Open one of the first papers you ingested — the brief now has more to compare against. The corpus is becoming denser.

---

## What's next

When you have roughly 15–20 notes on this topic (papers + claims combined), you're ready for a MOC — a Map of Content that gives the cluster a navigational hub. The threshold is in [reference/linking.md](../reference/linking.md#moc-thresholds).

When you're ready to write something from what you've built:

[Tutorial 05 — Start a writing project](05-start-a-writing-project.md): scope the corpus for a project, let Mapper produce a corpus map, choose a framing, and commit an outline.
