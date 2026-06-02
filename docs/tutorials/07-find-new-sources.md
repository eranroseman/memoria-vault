---
title: "Tutorial 07: Find new sources"
parent: Tutorials
---


# Tutorial 07: Find new sources

**You will end with:** a candidates queue with 5+ surfaced papers, at least one of them added to Zotero, ingested as a paper-note, and ready to classify.

**Time:** 25–35 minutes.

**You will use:** WSL2 terminal (Hermes CLI) and Obsidian.

**Prerequisite:** [Tutorial 04](04-build-a-reading-batch.md) complete. At least three classified paper-notes in your vault to use as seeds.

---

## Why this tutorial

Tutorials 03 and 04 showed you how to bring papers *you already knew about* into the vault. This tutorial shows the other direction: letting the system surface papers you haven't encountered yet, based on what's already there. This closes the knowledge cycle — the vault grows by accumulation, not just by what you happen to come across.

There are two complementary discovery paths. You'll use both:

- **Forward citations** — papers that *cite* one of your existing papers (what built on it)
- **Concept search** — papers matching a research question you phrase in your own words

---

## Step 1 — Choose a seed paper

Open `20-sources/01-papers/` in Obsidian. Pick a paper-note that's central to your current focus — well-classified, probably the most-linked one you have. Note its citekey (the filename without `.md`).

---

## Step 2 — Start the Librarian's find skill

Open WSL2 (or your terminal on Linux):

```bash
hermes -p memoria-librarian chat -s find
```

The `-s find` flag loads the discovery skill. Without it the Librarian answers questions about existing vault contents rather than running searches.

---

## Step 3 — Run a forward citation search

Inside the session:

```text
/find --source <your-citekey> --depth 1
```

Replace `<your-citekey>` with the citekey from Step 1.

**What happens:** the Librarian queries OpenAlex for papers that cite your seed. At `--depth 1` it returns first-order citations only — papers one hop away. This typically surfaces 20–80 candidates depending on how much your seed paper has been cited.

Watch the output. The Librarian scores each found paper for novelty against your existing vault (papers already in your notes are de-prioritized) and writes lightweight candidate notes to `10-inbox/03-candidates/`.

---

## Step 4 — Run a concept search

Still inside the same session:

```text
/find --query "your research question here" --limit 15
```

Write a short phrase describing a gap you want to fill. Use your own words — not paper titles, not keywords from your frontmatter. Examples:

- `"just-in-time interventions for physical activity"`
- `"receptivity prediction using context sensing"`
- `"longitudinal knowledge graph construction"`

The Librarian rewrites your query, runs hybrid retrieval (semantic + keyword against OpenAlex and Semantic Scholar), and adds more candidates.

You'll see different papers than the citation search returned — concept search finds papers that discuss the same ideas even if they never cite your seed.

After both searches complete:

```text
exit
```

---

## Step 5 — Review the candidates queue

Open `10-inbox/03-candidates/` in Obsidian. Each candidate note contains:

- **Title and abstract snippet** — what the paper is about
- **Relevance signal** — why the Librarian surfaced it (cites seed / cited by seed / concept match)
- **Novelty signal** — whether the paper introduces constructs your vault doesn't have yet

You don't have to read all of them now. Work through the 5–10 that look most relevant.

---

## Step 6 — Triage: include or exclude each candidate

For each candidate you review, make one decision.

**Include — worth reading and ingesting:**
1. Open the paper in a browser. The candidate note has a DOI or URL.
2. Add it to Zotero using the browser connector or by dragging the PDF.
3. Pin the citekey immediately: right-click the Zotero item → **Better BibTeX → Pin BibTeX key**. Pin before doing anything else — an unpinned key can drift if you edit metadata later.
4. Wait ~60 seconds for Better BibTeX's auto-export to update `memoria.bib`.
5. Delete the candidate note — it's been replaced by a real source about to be ingested.

**Exclude — not relevant, or already covered:**
Add to the candidate note's frontmatter:

```yaml
excluded: true
reason: "Already covered by <citekey> — same finding."
```

Keep the note in place. The Linter tracks exclusion coverage; an empty `reason` field is flagged.

Don't leave candidates undecided. The weekly review surfaces the count of candidates older than 7 days.

---

## Step 7 — Ingest the first included paper

For the first paper you added to Zotero in Step 6:

In Obsidian, with the Zotero item selected, `Cmd/Ctrl+P` → **Memoria: capture from Zotero selection**.

Open `00-meta/01-dashboards/reading-pipeline.md`. Within a minute, your paper appears with `lifecycle: proposed`.

This is the same ingest flow from Tutorial 03. The paper-note is now in your vault, ready to classify and discuss.

---

## What you have

- `10-inbox/03-candidates/` — new candidates with relevance signals, each either excluded (with a reason) or deleted (because ingested)
- At least one paper-note in `20-sources/01-papers/` with `lifecycle: proposed`
- A live sense of what the Librarian's discovery loop surfaces — not papers you searched for, but papers that connect to what you already know

---

## What you learned

The find workflow changes how the vault grows. Instead of importing papers you already knew about, you're letting the citation graph and semantic similarity pull in papers you didn't know to look for. As your corpus grows, the novelty signal becomes more discriminating — a richer vault means the Librarian can better distinguish what you need from what you already have.

Concept searches improve with practice. The more specific your query, the less noise in the candidates queue.

---

## What's next

Classify the new paper-note: [How to classify a source](../how-to-guides/sources/classify-a-source.md).

Process outstanding candidates as part of your Friday ritual: [How to run the weekly review](../how-to-guides/maintenance/run-the-weekly-review.md).

You've completed the tutorial sequence. The how-to guides cover every recurring task from here — see [how-to-guides/README.md](../how-to-guides/README.md).

---

← [Tutorial 06: Verify and address a gap](06-verify-and-address-gaps.md)
