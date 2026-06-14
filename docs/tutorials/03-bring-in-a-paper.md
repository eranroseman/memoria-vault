---
title: "Tutorial 03: Bring in a paper"
parent: Tutorials
---

# Tutorial 03: Bring in a paper

**You will end with:** one paper entity in `catalog/papers/`, one candidate card judged in the Inbox, and one proposed source note in `notes/source/` filled in your own words.

**Time:** 30–45 minutes (includes reading the paper or its abstract).

**You will use:** the Obsidian command palette and the Inbox.

**Prerequisite:** [Tutorial 02: Your first note](02-your-first-note.md) complete.

---

## Step 1 — Capture the paper

Pick a paper you actually want to read, and copy its URL (the publisher page, or anything that resolves to a DOI). In Obsidian press `Cmd/Ctrl+P` → **Memoria: capture source from URL** → paste the URL (a resolvable DOI ingests; a bare URL asks you for the DOI or citekey). That puts a capture card on the Librarian's `catalog` lane.

> **See also:** if you keep a [Zotero](https://www.zotero.org/) library, **Memoria: capture from Zotero selection** captures the selected item the same way — [Set up Zotero](../how-to-guides/zotero/set-up-zotero.md) is a one-time setup that gives you stable citekeys. Either route, and telling the Co-PI "bring in this paper: `<DOI>`", feeds the same `catalog` lane. See [Capture and ingest a source](../how-to-guides/compile/capture-and-ingest.md).

---

## Step 2 — What the ingest engine creates

Within a couple of minutes the deterministic ingest engine, driven by the Librarian, has:

- Created the **Catalog entity**: `catalog/papers/<citekey>.md` with `type: paper`, merged metadata (title, DOI, authors, year, venue — per-field provenance from Semantic Scholar, OpenAlex, and Crossref), and **`relationships`** edges — `authored_by`, `published_in`, `cites` — linking it to person, venue, and paper entities it finds or creates alongside.
- Recorded the source in the visible Catalog entity at `catalog/papers/<citekey>.md`; when full text is available, the engine keeps its private extract path in that entity's metadata.

Open `catalog/papers/<citekey>.md` and look at the `relationships` block — that's the knowledge graph's *given* edges, built by the engine. Your own `links:` come later, on notes you author. Full pipeline reference: [Ingest routing](../reference/ingest.md).

---

## Step 3 — Judge the candidate card

Capture doesn't end with a silent import: a **`candidate` card** lands in your Inbox proposing the keep. Load the **Desk** workspace — the card is in the Inbox tab's **Needs me** view — or open the file in `inbox/`.

The card carries the honesty body — an argument, never a verdict: an `action`, the case for and against, what tipped it, and a certainty level. Why a card argues instead of ruling: [The honesty card](../explanation/kanban-board/card-schema.md); the exact fields: [Frontmatter fields](../reference/frontmatter.md).

Read the `argument_against` case first — it's the information-bearing field. Then decide: keep it (set `lifecycle: proposed` to `current`) or skip it (set it straight to `archived` — the Catalog entry stays as a record). For this tutorial, keep it; you'll archive the card in Step 5 once you've acted on it.

---

## Step 4 — Read the paper

Read the paper, or at minimum the abstract and conclusions. Keep `catalog/papers/<citekey>.md` open in a split pane for the merged metadata, identifiers, and relationships while you read from the paper/PDF.

As you read, watch for one or two things worth keeping — not a summary of everything.

---

## Step 5 — Write the source note

The source note is *your* reading record — the literature note, in your words, never the agent's. The Librarian creates a proposed stub in `notes/source/` during ingest so the reading queue can see it; open that stub and fill its sections:

```yaml
type: source
lifecycle: proposed
entity: "[[<citekey>]]"
source_type: paper
```

- **`entity`** — the wikilink back to the Catalog entity from Step 2. Every source note is *about* exactly one Catalog entry.
- **`lifecycle: proposed`** — a source note starts proposed and advances as your distillation matures along the lifecycle chain (full chain and per-type subsets: [Frontmatter fields](../reference/frontmatter.md); the note types themselves: [Note types](../reference/note-types.md)).

Fill the three body sections the template gives you:

1. **In my words** — what the paper claims, on what evidence. Write it fresh; don't paste the abstract.
2. **Worth distilling** — candidate claims you might extract later (Tutorial 05 turns these into claim notes).
3. **Tensions** — where it disagrees with anything your vault already holds.

Save. Then resolve the candidate card from Step 3 — its job is done.

---

## What you have

- `catalog/papers/<citekey>.md` — the paper entity, with `relationships` edges into the Catalog
- A judged candidate card — you read an honest argument and made the call
- `notes/source/` — one source note stub filled in your own words, linked to its entity

The paper is a vault citizen; the source note is your intellectual claim on it.

---

## What's next

[Tutorial 04: Build a reading batch](04-build-a-reading-batch.md) — scale this flow to a topic: one reading queue, worked as a batch.

---

← [Tutorial 02: Your first note](02-your-first-note.md) · [Tutorial 04: Build a reading batch](04-build-a-reading-batch.md) →
