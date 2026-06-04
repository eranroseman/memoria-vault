---
title: "Tutorial 03: Bring in a paper"
parent: Tutorials
---


# Tutorial 03: Bring in a paper

**You will end with:** one `paper-note` in `20-sources/01-papers/` classified and promoted to `lifecycle: current`, and one `claim-note` in `30-synthesis/01-claims/` linked to it.

**Time:** 30–45 minutes (includes time to read the paper or its abstract).

**You will use:** Zotero, then Obsidian command palette and dashboards.

**Prerequisite:** [Tutorial 02](02-your-first-note.md) complete. Zotero open with Better BibTeX installed.

---

## Step 1 — Add the paper to Zotero

Add a paper to Zotero that you actually want to read — one relevant to your research area. If you're unsure which paper to use, choose a well-cited one in your field that you've been meaning to read.

Add it by:

- Dragging a PDF onto Zotero, or
- Using the Zotero browser connector on a journal page, or
- Using **File → Import** with a RIS or BibTeX file

After adding, verify that Zotero assigned a citekey (Better BibTeX should generate one automatically). The citekey appears in the **Extra** field of the Zotero item, formatted like `mamykina2010sense` — lowercase author name + year + first significant word of the title.

> **If the citekey hasn't appeared yet:** right-click the item → **Better BibTeX → Refresh BibTeX key**. If it still doesn't appear, check that Better BibTeX is installed (Tools → Add-ons).

Note the citekey. You'll need it in a moment.

---

## Step 2 — Hand the paper to the Librarian

In Obsidian, with Zotero open and the paper selected:

Press `Cmd+P` → type `capture zotero` → select **Memoria: capture from Zotero selection**.

**What happens:** Obsidian reads the current Zotero selection, creates an `intake:source` card on the Librarian lane, and confirms with a brief notification. The Librarian will pick up the card within 60 seconds.

---

## Step 3 — Watch the paper-note arrive

Open `00-meta/01-dashboards/reading-pipeline.md`.

Within about a minute, you'll see your paper appear with `lifecycle: proposed`. The Librarian has:

- Created a `paper-note` in `20-sources/01-papers/<citekey>.md`
- Populated the frontmatter from Zotero's metadata and the OpenAlex/Semantic Scholar APIs
- Extracted the PDF to `90-assets/extracts/<citekey>.md` (if the PDF is open-access or was imported into Zotero)
- Composed a `[!brief]` callout at the top of the paper-note — the Librarian's comparative read during ingest — comparing this paper against your existing vault (if you have other papers on related topics)
- Proposed a `_proposed_classification` block with suggested `topic`, `study_design`, and `methods` fields

Open the paper-note at `20-sources/01-papers/<citekey>.md`.

---

## Step 4 — Read the brief

At the top of the paper-note, find the `[!brief]` callout. Read it before opening the paper.

The brief tells you:

- Which of your existing notes this paper overlaps with
- Whether it might contradict something you've already noted
- Any new constructs it introduces that your vault doesn't have yet

If you have no other papers in the vault yet, the brief will be sparse. That's fine — it will grow more useful as your corpus grows.

---

## Step 5 — Read the paper (or the abstract)

Read the paper, or at minimum the abstract and conclusions. The extract at `90-assets/extracts/<citekey>.md` is a Markdown version of the full text — useful for reading on screen.

As you read, note in your head (or in a fleeting note) one or two things that stand out. You're not trying to document everything — you're looking for claims worth adding to your synthesis zone.

---

## Step 6 — Classify the paper-note

Open the paper-note. Find the `_proposed_classification` block in the frontmatter. It looks like:

```yaml
_proposed_classification:
  topic:
    - receptivity-detection
    - behavior-change
  study_design: field-study
  methods:
    - ema
    - interviews
```

Review each field. For each one:

- **If you agree:** move it to the main YAML frontmatter (the section before `_proposed_classification`)
- **If you'd use different terms:** change it before moving it
- **If a field is wrong:** delete it

After promoting the fields you agree with, delete the entire `_proposed_classification` block. Then change `lifecycle: proposed` to `lifecycle: current`.

Your frontmatter now looks like:

```yaml
type: paper-note
lifecycle: current
topic:
  - receptivity-detection
created: 2025-11-15
```

Save the note.

**Check the dashboard:** `reading-pipeline.md` now shows your paper as `lifecycle: current`. The reading pipeline has one fewer item in the `proposed` column.

**See also:** [Vocabulary discipline](../reference/linking.md#vocabulary-discipline) — guidelines for choosing and maintaining your topic terms.

---

## Step 7 — Discuss the paper with Socratic

With the paper-note open:

Open the agent-client pane (`Cmd+P` → **Agent Client: Open chat view**, or click the Hermes ribbon icon) and switch to **Socratic** (via the pane’s profile picker). *(A one-shot `Memoria: ask about this note` command is [deferred] — use the pane today.)*

The Socratic pane opens with the paper-note attached. Tell it: "I just read this paper. Help me think about what it means for my research."

Socratic will ask questions like:

- "What's the core claim this paper makes?"
- "What does it connect to in your existing thinking?"
- "What would you need to believe in order to trust this finding?"

Spend 5–10 minutes in conversation. Look for one clear, durable claim you want to add to your synthesis zone.

---

## Step 8 — Write one claim note

Press `Cmd+P` → type `write claim` → select **Memoria: write claim note**.

Fill in:

**Title:** Your claim, in one sentence, in your own words. Example: `Receptivity to notifications decreases when users are cognitively loaded`. This is *your claim*, not the paper's title or abstract.

**Body:** 2–4 sentences. What the claim means, why you believe it, what would overturn it.

**sources: frontmatter:** Add the citekey wikilink: `[[<your-citekey>]]`

**topic:** Use the same terms you used to classify the paper.

Save the claim note.

---

## Step 9 — Link the notes

Open the claim note. In the `sources:` frontmatter field you set in the previous step, the paper-note is linked.

Now open the paper-note and add a link to the claim note in its body, under a `## Claim notes` section at the bottom:

```markdown
## Claim notes

- [[your-claim-note-title]]
```

This bidirectional link is the knowledge graph forming. The paper points to what you extracted from it; the claim points back to its source.

---

## What you have

- `20-sources/01-papers/<citekey>.md` — classified, `lifecycle: current`, enriched
- `30-synthesis/01-claims/<your-claim>.md` — `maturity: seedling`, linked to the paper
- Reading pipeline dashboard: one item moved from `proposed` to `current`

The paper is now a vault citizen. The claim note is your intellectual contribution from it.

---

## What's next

[Tutorial 04 — Build a reading batch](04-build-a-reading-batch.md): repeat this flow for 5 papers on the same topic, write 3 linked claim notes, and see your first connected knowledge cluster take shape.

---

← [Tutorial 02: Your first note](02-your-first-note.md) · [Tutorial 04: Build a reading batch](04-build-a-reading-batch.md) →
