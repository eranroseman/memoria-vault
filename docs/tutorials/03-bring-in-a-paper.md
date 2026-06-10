---
title: "Tutorial 03: Bring in a paper"
parent: Tutorials
---

# Tutorial 03: Bring in a paper

**You will end with:** one paper entity in `catalog/papers/`, one candidate card judged in the Inbox, and one source note in `notes/source/` written in your own words.

**Time:** 30–45 minutes (includes reading the paper or its abstract).

**You will use:** the Obsidian command palette, the Inbox, and optionally Zotero.

**Prerequisite:** [Tutorial 02: Your first note](02-your-first-note.md) complete.

---

## Step 0 — Set up Zotero (optional, but recommended)

Zotero is Memoria's recommended bibliographic backbone — stable citekeys and a `.bib` file the ingest engine reads. You can skip this and capture from a URL instead (Step 1); come back when you adopt Zotero.

1. Install [Zotero](https://www.zotero.org/) and the [Better BibTeX](https://retorque.re/zotero-better-bibtex/) add-on.
2. **Citekeys are pinned automatically** by Better BibTeX — a generated key never regenerates, so vault wikilinks stay stable with no manual step.
3. Export your library to the vault: right-click the library → **Export Library** → format **Better BibLaTeX** → check **Keep updated** → save to `<your-vault>/.memoria/memoria.bib`.

That's the whole integration: Better BibTeX keeps `memoria.bib` current, and Memoria reads it. Details and connector options: [Zotero plugins](../reference/zotero-plugins.md) and [Set up Zotero](../how-to-guides/zotero/set-up-zotero.md).

---

## Step 1 — Capture the paper

Pick a paper you actually want to read. Then either:

- **From Zotero:** select the item in Zotero, and in Obsidian press `Cmd/Ctrl+P` → **Memoria: capture from Zotero selection**.
- **From a URL:** press `Cmd/Ctrl+P` → **Memoria: capture source from URL** and paste the paper's URL. A URL with a resolvable DOI ingests; a bare or proxied URL asks you for the DOI or citekey.

Either route puts a capture card on the Librarian's `catalog` lane. (Third option, no palette at all: tell the co-PI "bring in this paper: `<DOI>`" and it delegates the same card.)

---

## Step 2 — What the ingest engine creates

Within a couple of minutes the deterministic ingest engine, driven by the Librarian, has:

- Created the **Catalog entity**: `catalog/papers/<citekey>.md` with `type: paper`, merged metadata (title, DOI, authors, year, venue — per-field provenance from Semantic Scholar, OpenAlex, and Crossref), and **`relationships`** edges — `authored_by`, `published_in`, `cites` — linking it to person, venue, and paper entities it finds or creates alongside.
- Extracted the full text to `.memoria/data/extracts/<citekey>.md` where one is available.

Open `catalog/papers/<citekey>.md` and look at the `relationships` block — that's the knowledge graph's *given* edges, built by the engine. Your own `links:` come later, on notes you author. Full pipeline reference: [Ingest routing](../reference/ingest.md).

---

## Step 3 — Judge the candidate card

Capture doesn't end with a silent import: a **`candidate` card** lands in your Inbox proposing the keep. Open `home.md` — the card is in the **What needs me** view — or open the file in `inbox/`.

The card carries the honesty body — an argument, never a verdict ([The honesty card](../explanation/kanban-board/card-schema.md)):

- **`action`** — what you'd be accepting if you act
- **`argument_for`** — the case for keeping it
- **`argument_against`** — the agent's strongest honest self-rebuttal
- **`what_tipped_it`** — the single deciding reason
- **`certainty`** — `confident` / `likely` / `unsure`

Read the *against* case first — it's the information-bearing field. Then decide:

- **Keep:** set the card's `lifecycle: proposed` to `current` (then `archived` once you've acted on it below).
- **Skip:** set it straight to `archived`. The Catalog entry stays as a record; nothing else happens.

For this tutorial, keep it.

---

## Step 4 — Read the paper

Read the paper, or at minimum the abstract and conclusions. The extract at `.memoria/data/extracts/<citekey>.md` is a Markdown version of the full text, comfortable to read in a split pane.

As you read, watch for one or two things worth keeping — not a summary of everything.

---

## Step 5 — Write the source note

The source note is *your* reading record — the literature note, in your words, never the agent's. Create a new note in `notes/source/` from `system/templates/source.md` (or copy its shape):

```yaml
type: source
lifecycle: proposed
entity: "[[<citekey>]]"
source_type: paper
```

- **`entity`** — the wikilink back to the Catalog entity from Step 2. Every source note is *about* exactly one Catalog entry.
- **`lifecycle: proposed`** — a source note starts proposed and advances as your distillation matures (the full chain runs `proposed → provisional → current → retracted → archived`; see [Note types](../reference/note-types.md)).

Fill the three body sections the template gives you:

1. **In my words** — what the paper claims, on what evidence. Write it fresh; don't paste the abstract.
2. **Worth distilling** — candidate claims you might extract later (Tutorial 05 turns these into claim notes).
3. **Tensions** — where it disagrees with anything your vault already holds.

Save. Then archive the candidate card from Step 3 — its job is done.

---

## What you have

- `catalog/papers/<citekey>.md` — the paper entity, with `relationships` edges into the Catalog
- A judged candidate card — you read an honest argument and made the call
- `notes/source/` — one source note in your own words, linked to its entity

The paper is a vault citizen; the source note is your intellectual claim on it.

---

## What's next

[Tutorial 04: Build a reading batch](04-build-a-reading-batch.md) — scale this flow to a topic: one reading queue, worked as a batch.

---

← [Tutorial 02: Your first note](02-your-first-note.md) · [Tutorial 04: Build a reading batch](04-build-a-reading-batch.md) →
