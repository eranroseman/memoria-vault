---
title: "Tutorial 02: Bring in your first source"
parent: Tutorials
---

# Tutorial 02: Bring in your first source

*Session 1 of 3 · Build a starter corpus.*

**You'll finish with:** one source of your own in the catalog, the card it raises in your Inbox judged, and a source note written in your own words. Your first source brought in start to finish, sitting next to the sample's worked examples.

**Time:** 30–45 minutes (includes reading the paper or its abstract).

**You'll use:** the Obsidian command palette, the Inbox, and the Agent Client pane.

**Prerequisite:** [Tutorial 01: See what you're building](01-see-what-you-are-building.md) complete — the sample vault loaded and a project opened over it.

---

Turning what you read into durable, traceable notes is the habit at the center of Memoria, and you learn a habit by doing it. The sample vault gives you finished source notes to study, but the move only sticks once you do it on your own material — so in this tutorial you bring in a source of your own.

The sample came with finished source notes — the PREDIMED note, the Lyon Diet Heart note, and others. Open the **Library** space and you'll see them in the Reading pipeline, already filled in. Keep one open in a split pane as you work: it shows the shape you're aiming for, not text to copy.

## Step 1 — Capture your source

Pick a paper you actually want to read for your own goal, and copy its URL — the publisher page, or any link that resolves to a DOI. In Obsidian, press `Cmd/Ctrl-P` → **Memoria: capture source from URL** and paste it. A URL with a clear DOI comes in right away; a plain URL asks you for the DOI or citekey first. Either way, your request goes to the **Librarian** — the background worker that looks after your catalog.

> **See also:** if you keep a [Zotero](https://www.zotero.org/) library, **Memoria: capture from Zotero selection** brings in the selected item the same way — [Set up Zotero](../how-to-guides/zotero/set-up-zotero.md) is a one-time setup that gives you stable citekeys. Not sure what to capture? Ask the Co-PI to help shape the request, then run the matching command. Both commands feed the same place.

---

## Step 2 — What capturing creates

Within a couple of minutes, the Librarian has finished bringing the paper in. It has:

- Created the **catalog entity** — Memoria's record of the paper itself, at `catalog/papers/<citekey>.md`. It holds `type: paper`, the merged metadata (title, DOI, authors, year, venue — each field tracing back to where it came from: Semantic Scholar, OpenAlex, Crossref, or PubMed/NCBI), and a **`relationships`** block linking the paper to its authors, its venue, and the papers it cites — each of those a record Memoria finds or creates alongside.
- Created a **source note** for it (still just a stub) in `notes/sources/`, so it shows up in your reading queue.

Open the **Library** space, find your new paper in its **Catalog** view (`catalog.base`), and look at the `relationships` block. These links came for free, from the paper's own metadata — the links *you* make come later, on the notes you write. Compare it to one of the sample's papers: same shape, real metadata. After the tutorial, the full pipeline contract is in [Ingest routing](../reference/ingest.md).

---

## Step 3 — Judge the candidate card

Bringing a paper in doesn't happen silently: a **candidate card** lands in your Inbox, with Memoria proposing that you keep this source and asking you to decide. Open the **Inbox queue** → **Needs me** view.

The card makes an argument, not a ruling: a proposed `action`, the case for and against, what tipped the balance, and how certain it is. Read the `argument_against` field first — it's the one that actually tells you something. Then decide, and resolve the card from the palette: `Cmd/Ctrl-P` → **Memoria: resolve inbox card**. For this tutorial, keep the source (`current`). If you skip one instead, its card goes to `archived` and the catalog record stays as a trace. Why a card argues instead of ruling: [The honesty card](../explanation/kanban-board/honesty-card.md).

---

## Step 4 — Read it, then write the source note in your own words

Read the paper — or at least its abstract and conclusions — with its catalog entity open in a split pane (from the **Library** space's **Catalog** view) for the metadata and links. Watch for one or two things worth keeping, not a summary of everything.

Then open the source note from the **Library** space's Reading pipeline. This note is *your* reading record — written in your words, never the agent's. Behind the scenes it carries a small frontmatter header:

```yaml
type: source
lifecycle: proposed
entity: "[[<citekey>]]"
source_type: paper
```

For now, just notice that `entity` points back to the paper record and `lifecycle` says the note still needs work. The full field list is in [Frontmatter fields](../reference/frontmatter.md).

Fill in the three sections the template gives you. This is where the sample notes earn their keep: open the **PREDIMED** source note (`estruch2018-predimed`) beside yours, notice *how* it's written, and write yours the same way about your own paper:

1. **In my words** — what the paper claims, and on what evidence. Write it fresh; don't paste the abstract. (See how the PREDIMED note lays out the trial, its arms, and the result in plain sentences.)
2. **Worth distilling** — one or two claims you might pull out later. Each bullet is a future claim note; use the **Create linked claim** button when a sentence is ready.
3. **Tensions** — where this paper disagrees with anything already in your vault. Does it touch the same cause-versus-confounding tension the sample's cluster holds? Note it.

Save, then set the source note to `lifecycle: provisional` — read and recorded in your words, but not yet turned into claims. Once you distill the claims you need (next tutorial), you'll move it to `current`.

---

## A note on stray thoughts: fleeting notes

Not every thought comes attached to a source. When something occurs to you mid-read with no citation behind it — a hunch, a question, a connection — capture it as a **fleeting note** (`Cmd/Ctrl-P` → **Memoria: capture fleeting**). It's the lightest note there is: one thought, no quality bar. It shows up in the Inbox later, to be turned into a real note or archived. That's all a fleeting note is — a holding pen for un-sourced sparks, not where your knowledge lives. Sourced reading is the backbone; keep your attention there.

---

## What you have

- `catalog/papers/<citekey>.md` — your own paper, with `relationships` links into the catalog
- A candidate card judged — you read an honest argument and decided
- One source note of your own (now `provisional`), written in your words and linked to its paper
- The sample's worked source notes still beside it as models

The paper is now part of your vault; the source note is your own reading of it. You've done this once — the months of real work are just this, repeated.

---

## What's next

[Tutorial 03: Build claims and connect them](03-build-claims-and-connect-them.md) — study a worked claim in the sample, finish its half-built claims and links, then distill a claim from your own source and connect it to the cluster.

---

← [Tutorial 01: See what you're building](01-see-what-you-are-building.md) · [Tutorial 03: Build claims and connect them](03-build-claims-and-connect-them.md) →
